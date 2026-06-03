"""Etat partage entre les blueprints : task, logs, helpers."""
import os
import sys
import queue
import threading
import logging
import subprocess
from logging.handlers import RotatingFileHandler
from pathlib import Path

log_queue = queue.Queue(maxsize=1000)
current_task = {"running": False, "name": "", "progress": 0}
task_lock = threading.Lock()

_current_process = None
_process_lock = threading.Lock()

# Diffusion d'evenements de tache aux abonnes SSE (un Queue par client connecte).
_task_subscribers = []
_task_subscribers_lock = threading.Lock()


def subscribe_task_events():
    q = queue.Queue(maxsize=100)
    with _task_subscribers_lock:
        _task_subscribers.append(q)
    return q


def unsubscribe_task_events(q):
    with _task_subscribers_lock:
        try:
            _task_subscribers.remove(q)
        except ValueError:
            pass


def _broadcast_task():
    with task_lock:
        snapshot = dict(current_task)
    with _task_subscribers_lock:
        for q in list(_task_subscribers):
            try:
                q.put_nowait(snapshot)
            except queue.Full:
                pass


# Sentinelle diffusee avant l'arret du serveur pour permettre aux clients SSE
# de fermer proprement leur connexion (sans tenter de se reconnecter en boucle).
SHUTDOWN_SENTINEL = "__shutdown__"


def broadcast_shutdown():
    """Pousse une sentinelle a tous les abonnes SSE (logs + taches).

    Apres reception, le client doit fermer son EventSource et ne pas reconnecter.
    """
    # Canal task : envoie un dict reconnaissable
    with _task_subscribers_lock:
        for q in list(_task_subscribers):
            try:
                q.put_nowait({"__shutdown__": True})
            except queue.Full:
                pass
    # Canal logs : envoie une ligne sentinelle
    try:
        log_queue.put_nowait(SHUTDOWN_SENTINEL)
    except queue.Full:
        pass

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            log_queue.put_nowait(self.format(record))
        except queue.Full:
            pass


_log_file_handler = RotatingFileHandler(
    LOG_DIR / "mintyforge.log",
    maxBytes=2_000_000,   # 2 MB par fichier
    backupCount=3,        # mintyforge.log + .1 .2 .3
    encoding="utf-8",
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[_log_file_handler, QueueHandler()],
)
logger = logging.getLogger("mintyforge")


def log_info(msg):    logger.info(msg)
def log_success(msg): logger.info(f"[OK] {msg}")
def log_warn(msg):    logger.warning(f"[WARN] {msg}")
def log_error(msg):   logger.error(f"[ERROR] {msg}")


def notify_desktop(title, message=""):
    try:
        subprocess.run(
            ["notify-send", "-a", "MintyForge", "-i", "dialog-information", title, message],
            capture_output=True, timeout=3
        )
    except Exception:
        pass


def update_task_status(name, running, progress=0):
    with task_lock:
        was_running = current_task["running"]
        current_task["name"] = name
        current_task["running"] = running
        current_task["progress"] = progress
    _broadcast_task()
    if was_running and not running and progress == 100:
        notify_desktop("Termine", name)


def set_current_process(proc):
    global _current_process
    with _process_lock:
        _current_process = proc


def cancel_current_task():
    """Tue le processus en cours."""
    global _current_process
    with _process_lock:
        if _current_process and _current_process.poll() is None:
            _current_process.kill()
            _current_process = None
            return True
        return False


def run_script(script_name):
    script_path = Path("scripts") / f"{script_name}.py"
    if not script_path.exists():
        script_path = Path("scripts") / script_name
        if not script_path.exists():
            log_error(f"Script introuvable : {script_name}")
            return False
    try:
        log_info(f"Lancement de {script_name}...")
        cmd = [sys.executable, str(script_path)] if script_path.suffix == ".py" else ["bash", str(script_path)]
        env = {**os.environ, "PYTHONUNBUFFERED": "1"}
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=env
        )
        set_current_process(process)
        for line in process.stdout:
            line = line.rstrip('\n')
            if line.strip():
                log_info(line)
        process.wait(timeout=1800)
        set_current_process(None)
        if process.returncode == 0:
            log_success(f"Termine : {script_name}")
            return True
        if process.returncode is not None and process.returncode < 0:
            log_warn(f"Annule : {script_name}")
            return False
        log_error(f"Echec : {script_name} (code {process.returncode})")
        return False
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        set_current_process(None)
        log_error(f"Timeout : {script_name} (>30 min)")
        return False
    except Exception as e:
        set_current_process(None)
        log_error(f"Erreur {script_name} : {e}")
        return False
