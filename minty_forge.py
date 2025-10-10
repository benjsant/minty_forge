#!/usr/bin/env python3
"""
MintyForge – Main Script (Cinnamon Edition)
Robust version: calls Python scripts or shell scripts, exits curses cleanly
and returns to the interactive menu.
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

# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------
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
    # safe logging
    level_name = level if level in logging._nameToLevel else "info"
    getattr(logging, level_name)(msg)


def check_internet_connection(host="archive.ubuntu.com", port=80, timeout=2):
    """Checks if an Internet connection is available."""
    try:
        socket.create_connection((host, port), timeout=timeout)
        log_and_print("Internet connection detected.", "success")
        return True
    except OSError:
        log_and_print("No Internet connection detected. Please connect and retry.", "error")
        return False


def disable_suspend_and_screensaver():
    """Disables suspend and screensaver temporarily."""
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
    """Runs apt update and upgrade."""
    log_and_print("Updating system packages...", "info")
    subprocess.run(["sudo", "apt", "update", "-y"], check=False)
    subprocess.run(["sudo", "apt", "upgrade", "-y"], check=False)
    log_and_print("System updated.", "success")


# ---------------------------------------------------------------------
# Robust run_script which supports Python scripts and executables
# ---------------------------------------------------------------------
SCRIPTS_DIR = Path("scripts")
ROOT = Path(".").resolve()

def find_script_candidates(script_name: str):
    """
    Look for likely file paths for the requested script name.
    Returns the first path that exists or None.
    Order:
      - scripts/<script_name>.py
      - scripts/<script_name>
      - <script_name>.py (project root)
      - ./<script_name> (project root)
    """
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
    """
    Run the requested script. Detects .py and runs with python3, runs executables directly,
    otherwise falls back to bash <path>.
    This function will:
      - exit curses mode (curses.endwin())
      - run the script while showing output in the terminal
      - wait for user to press Enter
      - reinitialize curses (caller will continue)
    """
    path = find_script_candidates(script_name)
    if path is None:
        # nothing found, try legacy fallback (scripts/<script_name> as text)
        path_fallback = SCRIPTS_DIR / script_name
        if not path_fallback.exists():
            log_and_print(f"Script not found: searched for {script_name} in scripts/ and project root.", "error")
            return
        path = path_fallback

    log_and_print(f"Resolved script: {path}", "info")

    # End curses mode cleanly before running external program
    try:
        curses.endwin()
    except Exception:
        pass

    # Decide how to execute
    try:
        if path.suffix == ".py":
            log_and_print(f"Running Python script: {path}", "info")
            proc = subprocess.run(["python3", str(path)], check=False)
        elif os.access(str(path), os.X_OK):
            log_and_print(f"Running executable: {path}", "info")
            proc = subprocess.run([str(path)], check=False)
        else:
            # fallback to bash execution (supports .sh or plain script text)
            log_and_print(f"Running via bash: {path}", "info")
            proc = subprocess.run(["bash", str(path)], check=False)
    except Exception as e:
        log_and_print(f"Error while running {path}: {e}", "error")
    else:
        if proc.returncode == 0:
            log_and_print(f"{script_name} finished successfully.", "success")
        else:
            log_and_print(f"{script_name} exited with code {proc.returncode}.", "warn")

    # Keep output visible until user confirms
    try:
        input("\nPress ENTER to return to MintyForge menu...")
    except Exception:
        pass

    # Reinitialize curses environment for the calling wrapper
    try:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        if curses.has_colors():
            curses.start_color()
        curses.curs_set(0)
    except Exception:
        # If re-init fails, just continue; wrapper will recreate on next loop
        pass


# ---------------------------------------------------------------------
# Curses-based menu
# ---------------------------------------------------------------------
MENU_OPTIONS = [
    "Install APT packages",
    "Remove unwanted APT packages",
    "Install Flatpaks",
    "Install User Themes (GTK, Icons, Cursors)",
    "Configure Drivers",
    "Configure Qt Apps",
    "Run Distroscript",
    "Exit",
]


def curses_menu(stdscr):
    """Displays the interactive curses menu."""
    curses.curs_set(0)
    # initialize color pairs if possible
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)

    current_row = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        title = "🛠️  MintyForge Menu"
        if curses.has_colors():
            stdscr.attron(curses.color_pair(2))
        stdscr.addstr(1, max(0, width // 2 - len(title) // 2), title)
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
        elif key in [10, 13]:  # Enter key
            if current_row == len(MENU_OPTIONS) - 1:  # Exit
                log_and_print("Exiting MintyForge. Goodbye!", "success")
                time.sleep(0.2)
                break
            else:
                # map menu index -> script base name
                mapping = {
                    0: "apt_install",
                    1: "apt_remove",
                    2: "flatpak_install",
                    3: "themes_install",
                    4: "drivers",
                    5: "qt_install",
                    6: "distroscript",
                }
                script_name = mapping.get(current_row)
                if script_name:
                    stdscr.clear()
                    stdscr.addstr(2, 2, f"Running: {MENU_OPTIONS[current_row]} ...")
                    stdscr.refresh()
                    run_script(script_name)
                else:
                    log_and_print("No script mapped for this option.", "warn")
        elif key in [ord("q"), ord("Q")]:
            log_and_print("Exiting MintyForge. Goodbye!", "success")
            break


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    """Main entry point."""
    if not check_internet_connection():
        return
    disable_suspend_and_screensaver()
    update_system()

    # Setup curses menu
    curses.wrapper(curses_menu)


if __name__ == "__main__":
    main()
