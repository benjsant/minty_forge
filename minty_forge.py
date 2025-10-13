#!/usr/bin/env python3
"""
MintyForge – Main Script (Cinnamon Edition)
-------------------------------------------
Menu principal robuste basé sur curses.
Exécute des scripts shell ou Python de manière isolée, puis revient proprement au menu.
"""

import curses
import os
import subprocess
import logging
import time
import socket
from pathlib import Path

# ---------------------------------------------------------------------
# Setup logging
# ---------------------------------------------------------------------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "mintyforge.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def log_and_print(msg: str, level: str = "info"):
    """Logs and prints a message."""
    color_prefix = {
        "info": "[INFO] ",
        "success": "[OK] ",
        "warn": "[WARN] ",
        "error": "[ERROR] ",
    }
    prefix = color_prefix.get(level, "")
    print(f"{prefix}{msg}")
    level_name = level if level in logging._nameToLevel else "info"
    getattr(logging, level_name)(msg)

# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------
def check_internet_connection(host="archive.ubuntu.com", port=80, timeout=2):
    """Check internet availability."""
    try:
        socket.create_connection((host, port), timeout=timeout)
        log_and_print("Internet connection detected.", "success")
        return True
    except OSError:
        log_and_print("No Internet connection detected. Please connect and retry.", "error")
        return False

def disable_suspend_and_screensaver():
    """Disable suspend and screensaver temporarily."""
    log_and_print("Disabling suspend and screensaver temporarily...", "info")
    commands = [
        ["gsettings", "set", "org.cinnamon.settings-daemon.plugins.power", "sleep-inactive-ac-timeout", "0"],
        ["gsettings", "set", "org.cinnamon.settings-daemon.plugins.power", "sleep-inactive-battery-timeout", "0"],
        ["gsettings", "set", "org.cinnamon.desktop.screensaver", "lock-enabled", "false"],
    ]
    for cmd in commands:
        subprocess.run(cmd, check=False)
    log_and_print("Suspend and screensaver disabled.", "success")

def update_system():
    """Update apt packages."""
    log_and_print("Updating system packages...", "info")
    subprocess.run(["sudo", "apt", "update", "-y"], check=False)
    subprocess.run(["sudo", "apt", "upgrade", "-y"], check=False)
    log_and_print("System updated.", "success")

# ---------------------------------------------------------------------
# Script runner
# ---------------------------------------------------------------------
SCRIPTS_DIR = Path("scripts")
ROOT = Path(".").resolve()

def find_script_candidates(script_name: str):
    """Locate the correct path for a script."""
    candidates = [
        SCRIPTS_DIR / f"{script_name}.py",
        SCRIPTS_DIR / script_name,
        ROOT / f"{script_name}.py",
        ROOT / script_name,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def run_script(script_name: str):
    """Run a given script and return cleanly to curses menu."""
    path = find_script_candidates(script_name)
    if not path:
        log_and_print(f"Script not found: {script_name}", "error")
        return

    log_and_print(f"Resolved script: {path}", "info")

    try:
        curses.endwin()  # Leave curses before running
    except Exception:
        pass

    try:
        if path.suffix == ".py":
            log_and_print(f"Running Python script: {path}", "info")
            subprocess.run(["python3", str(path)], check=False)
        elif os.access(str(path), os.X_OK):
            log_and_print(f"Running executable: {path}", "info")
            subprocess.run([str(path)], check=False)
        else:
            log_and_print(f"Running via bash: {path}", "info")
            subprocess.run(["bash", str(path)], check=False)
    except Exception as e:
        log_and_print(f"Error while running {path}: {e}", "error")
    else:
        log_and_print(f"{script_name} finished.", "success")

    # Wait for user confirmation
    try:
        input("\nPress ENTER to return to MintyForge menu...")
    except Exception:
        pass

    # Reinit curses
    try:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        if curses.has_colors():
            curses.start_color()
        curses.curs_set(0)
    except Exception:
        pass

# ---------------------------------------------------------------------
# Menu configuration
# ---------------------------------------------------------------------
MENU_OPTIONS = [
    "Install APT packages",
    "Install External packages (optional)",
    "Remove unwanted APT packages",
    "Install Flatpaks",
    "Install User Themes (GTK, Icons, Cursors)",
    "Configure Drivers",
    "Run DistroScript",
    "Exit",
]

SCRIPT_MAPPING = {
    0: "apt_install",
    1: "external_install",
    2: "apt_remove",
    3: "flatpak_install",
    4: "themes_install",
    5: "drivers",
    6: "distroscript_install",
}

# ---------------------------------------------------------------------
# Curses Menu
# ---------------------------------------------------------------------
def curses_menu(stdscr):
    """Display interactive curses menu."""
    curses.curs_set(0)
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)

    current_row = 0
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        title = "🛠️  MintyForge Main Menu"
        if curses.has_colors():
            stdscr.attron(curses.color_pair(2))
        stdscr.addstr(1, width // 2 - len(title) // 2, title)
        if curses.has_colors():
            stdscr.attroff(curses.color_pair(2))

        for idx, row in enumerate(MENU_OPTIONS):
            x = max(0, width // 2 - len(row) // 2)
            y = 3 + idx
            if idx == current_row and curses.has_colors():
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, row)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(MENU_OPTIONS) - 1:
            current_row += 1
        elif key in [10, 13]:  # Enter
            if current_row == len(MENU_OPTIONS) - 1:  # Exit
                log_and_print("Exiting MintyForge. Goodbye!", "success")
                time.sleep(0.3)
                break
            else:
                script_name = SCRIPT_MAPPING.get(current_row)
                if script_name:
                    stdscr.clear()
                    stdscr.addstr(2, 2, f"Running: {MENU_OPTIONS[current_row]} ...")
                    stdscr.refresh()
                    run_script(script_name)
                else:
                    log_and_print("No script mapped to this option.", "warn")
        elif key in [ord("q"), ord("Q")]:
            log_and_print("Exiting MintyForge. Goodbye!", "success")
            break

# ---------------------------------------------------------------------
# Main Entry
# ---------------------------------------------------------------------
def main():
    """MintyForge entrypoint."""
    if not check_internet_connection():
        return
    disable_suspend_and_screensaver()
    update_system()
    curses.wrapper(curses_menu)

if __name__ == "__main__":
    main()
