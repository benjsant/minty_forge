"""Etat partage entre les blueprints : task, logs, helpers."""
import os
import sys
import queue
import threading
import logging
import subprocess
from pathlib import Path

log_queue = queue.Queue(maxsize=1000)
current_task = {"running": False, "name": "", "progress": 0}
task_lock = threading.Lock()

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            log_queue.put_nowait(self.format(record))
        except queue.Full:
            pass


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "mintyforge.log"), QueueHandler()]
)
logger = logging.getLogger("mintyforge")


def log_info(msg):    logger.info(msg)
def log_success(msg): logger.info(f"✅ {msg}")
def log_warn(msg):    logger.warning(f"⚠️ {msg}")
def log_error(msg):   logger.error(f"❌ {msg}")


def update_task_status(name, running, progress=0):
    with task_lock:
        current_task["name"] = name
        current_task["running"] = running
        current_task["progress"] = progress


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
        for line in process.stdout:
            line = line.rstrip('\n')
            if line.strip():
                log_info(line)
        process.wait(timeout=1800)
        if process.returncode == 0:
            log_success(f"Termine : {script_name}")
            return True
        log_error(f"Echec : {script_name} (code {process.returncode})")
        return False
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        log_error(f"Timeout : {script_name} (>30 min)")
        return False
    except Exception as e:
        log_error(f"Erreur {script_name} : {e}")
        return False
