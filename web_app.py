#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Web Interface (Flask Edition)
------------------------------------------
Simple Flask web interface to replace curses menu.
Compatible with Python 3.10+ (default on Linux Mint).
Provides a modern web UI to execute all installation tasks.
"""

import os
import subprocess
import json
import logging
import threading
import queue
import time
from pathlib import Path
from flask import Flask, render_template, jsonify, request, Response
from datetime import datetime

# Import secure subprocess utilities
import sys
sys.path.insert(0, str(Path(__file__).parent))
from utils import apt_update, apt_upgrade, run_python_script, run_bash_script
from utils.theme_manager import ThemeManager

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
app = Flask(__name__, 
            template_folder='web/templates',
            static_folder='web/static')

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "mintyforge.log"

# Queue for real-time log streaming
log_queue = queue.Queue()
current_task = {"running": False, "name": "", "progress": 0}
task_lock = threading.Lock()

# ---------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------
class QueueHandler(logging.Handler):
    """Custom handler to push logs to queue for web streaming."""
    def emit(self, record):
        log_entry = self.format(record)
        log_queue.put(log_entry)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        QueueHandler()
    ]
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------
def log_info(msg):
    logger.info(msg)

def log_success(msg):
    logger.info(f"✅ {msg}")

def log_warn(msg):
    logger.warning(f"⚠️  {msg}")

def log_error(msg):
    logger.error(f"❌ {msg}")

def run_script(script_name: str):
    """Execute a Python script from scripts/ directory."""
    script_path = Path("scripts") / f"{script_name}.py"
    
    if not script_path.exists():
        # Try without .py extension (for shell scripts)
        script_path = Path("scripts") / script_name
        if not script_path.exists():
            log_error(f"Script not found: {script_name}")
            return False
    
    try:
        log_info(f"Starting {script_name}...")
        
        if script_path.suffix == ".py":
            result = subprocess.run(
                ["python3", str(script_path)],
                capture_output=True,
                text=True
            )
        else:
            result = subprocess.run(
                ["bash", str(script_path)],
                capture_output=True,
                text=True
            )
        
        # Stream output to logs
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    log_info(line)
        
        if result.stderr:
            for line in result.stderr.split('\n'):
                if line.strip():
                    log_warn(line)
        
        if result.returncode == 0:
            log_success(f"Completed: {script_name}")
            return True
        else:
            log_error(f"Failed: {script_name} (exit code {result.returncode})")
            return False
            
    except Exception as e:
        log_error(f"Exception running {script_name}: {e}")
        return False

def update_task_status(name: str, running: bool, progress: int = 0):
    """Update current task status thread-safely."""
    with task_lock:
        current_task["name"] = name
        current_task["running"] = running
        current_task["progress"] = progress

# ---------------------------------------------------------------------
# System checks
# ---------------------------------------------------------------------
def check_system():
    """Check system prerequisites."""
    checks = {
        "internet": False,
        "sudo": False,
        "python_version": False
    }
    
    # Internet check
    try:
        import socket
        socket.create_connection(("archive.ubuntu.com", 80), timeout=3)
        checks["internet"] = True
    except:
        pass
    
    # Sudo check
    try:
        result = subprocess.run(["sudo", "-n", "true"], 
                              capture_output=True, 
                              timeout=1)
        checks["sudo"] = result.returncode == 0
    except:
        pass
    
    # Python version check
    import sys
    checks["python_version"] = sys.version_info >= (3, 8)
    
    return checks

def get_package_counts():
    """Get counts of packages to install from JSON configs."""
    counts = {}
    
    config_files = {
        "apt": "configs/install.json",
        "flatpak": "configs/flatpak.json",
        "external": "configs/external_packages.json",
        "themes_gtk": "configs/themes_gtk.json",
        "themes_icons": "configs/themes_icons.json",
        "themes_cursors": "configs/themes_cursors.json"
    }
    
    for key, path in config_files.items():
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                if 'packages' in data:
                    counts[key] = len(data['packages'])
                elif 'flatpaks' in data:
                    counts[key] = len(data['flatpaks'])
                elif 'themes' in data:
                    counts[key] = len(data['themes'])
                else:
                    counts[key] = 0
        except:
            counts[key] = 0
    
    return counts

# ---------------------------------------------------------------------
# Flask Routes
# ---------------------------------------------------------------------
@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/status')
def status():
    """Get current system status and task info."""
    return jsonify({
        "checks": check_system(),
        "packages": get_package_counts(),
        "task": current_task
    })

@app.route('/api/logs/stream')
def stream_logs():
    """Server-Sent Events endpoint for real-time logs."""
    def generate():
        while True:
            try:
                # Wait for new log with timeout
                log_msg = log_queue.get(timeout=1)
                yield f"data: {log_msg}\n\n"
            except queue.Empty:
                # Send keepalive
                yield f": keepalive\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/execute/<action>', methods=['POST'])
def execute_action(action):
    """Execute a specific action."""
    
    action_map = {
        "apt_install": "apt_install",
        "apt_remove": "apt_remove",
        "flatpak_install": "flatpak_install",
        "themes_install": "themes_install",
        "external_install": "external_install",
        "drivers": "drivers",
        "distroscript": "distroscript_install"
    }
    
    if action not in action_map:
        return jsonify({"success": False, "error": "Unknown action"}), 400
    
    with task_lock:
        if current_task["running"]:
            return jsonify({"success": False, "error": "Task already running"}), 409
    
    def run_task():
        update_task_status(action, True, 0)
        success = run_script(action_map[action])
        update_task_status("", False, 100)
        return success
    
    # Run in background thread
    thread = threading.Thread(target=run_task, daemon=True)
    thread.start()
    
    return jsonify({"success": True, "message": f"Started {action}"})

@app.route('/api/execute/all', methods=['POST'])
def execute_all():
    """Execute all installation tasks in sequence."""
    
    with task_lock:
        if current_task["running"]:
            return jsonify({"success": False, "error": "Task already running"}), 409
    
    def run_all_tasks():
        tasks = [
            ("System Update", "system_update"),
            ("APT Packages", "apt_install"),
            ("External Packages", "external_install"),
            ("Remove Bloat", "apt_remove"),
            ("Flatpak Install", "flatpak_install"),
            ("Themes Install", "themes_install"),
            ("Drivers", "drivers")
        ]
        
        total = len(tasks)
        
        for idx, (name, task) in enumerate(tasks):
            update_task_status(name, True, int((idx / total) * 100))
            log_info(f"=== Starting: {name} ({idx+1}/{total}) ===  ")
            
            if task == "system_update":
                # Use secure utils functions for system update
                log_info("Updating APT...")
                apt_update()
                log_info("Upgrading packages...")
                apt_upgrade()
            else:
                # Script execution
                run_script(task)
            
            time.sleep(0.5)  # Small delay between tasks
        
        update_task_status("All tasks completed!", False, 100)
        log_success("🎉 Full installation completed!")
    
    # Run in background
    thread = threading.Thread(target=run_all_tasks, daemon=True)
    thread.start()
    
    return jsonify({"success": True, "message": "Started full installation"})

@app.route('/api/theme/status')
def theme_status():
    """Get theme configuration status."""
    try:
        theme_manager = ThemeManager()
        config_file = Path("configs") / "theme_config_recommended.json"
        
        if not config_file.exists():
            return jsonify({
                "success": False,
                "error": "Configuration file not found"
            }), 404
        
        result = theme_manager.check_recommended_config(config_file)
        return jsonify({
            "success": True,
            "config": result
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/theme/apply_recommended', methods=['POST'])
def apply_recommended_theme():
    """Apply recommended theme configuration."""
    
    with task_lock:
        if current_task["running"]:
            return jsonify({
                "success": False,
                "error": "Task already running"
            }), 409
    
    def run_theme_task():
        update_task_status("Configuration Thèmes Recommandée", True, 0)
        
        try:
            theme_manager = ThemeManager()
            config_file = Path("configs") / "theme_config_recommended.json"
            
            if not config_file.exists():
                log_error("Configuration file not found")
                update_task_status("", False, 0)
                return False
            
            log_info("🎨 Application de la configuration recommandée...")
            update_task_status("Configuration Thèmes Recommandée", True, 20)
            
            # Appliquer la configuration (installe les thèmes manquants)
            success, messages = theme_manager.apply_recommended_config(
                config_file,
                install_missing=True
            )
            
            # Logger chaque message
            for msg in messages:
                if "✅" in msg:
                    log_success(msg)
                elif "❌" in msg:
                    log_error(msg)
                elif "⚠️" in msg:
                    log_warn(msg)
                else:
                    log_info(msg)
                
                # Update progress progressivement
                current_progress = current_task.get("progress", 20)
                if current_progress < 90:
                    update_task_status(
                        "Configuration Thèmes Recommandée",
                        True,
                        current_progress + 10
                    )
                    time.sleep(0.2)
            
            if success:
                log_success("🎉 Configuration des thèmes appliquée avec succès !")
                update_task_status("Configuration terminée", False, 100)
            else:
                log_error("⚠️  Configuration terminée avec des erreurs")
                update_task_status("Erreurs détectées", False, 100)
            
            return success
        
        except Exception as e:
            log_error(f"Erreur lors de la configuration : {str(e)}")
            update_task_status("", False, 0)
            return False
    
    # Run in background thread
    thread = threading.Thread(target=run_theme_task, daemon=True)
    thread.start()
    
    return jsonify({
        "success": True,
        "message": "Configuration des thèmes démarrée"
    })

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """Clear log display (doesn't delete log file)."""
    # Clear the queue
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except queue.Empty:
            break
    
    return jsonify({"success": True})

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    """Start Flask development server."""
    log_info("🚀 MintyForge Web Interface starting...")
    log_info("Open http://localhost:5000 in your browser")
    log_info("Press CTRL+C to stop")
    
    app.run(
        host='0.0.0.0',  # Accessible from network
        port=5000,
        debug=False,  # Set to True for development
        threaded=True
    )

if __name__ == '__main__':
    main()
