#!/usr/bin/env python3
"""
MintyForge – Main Script (Cinnamon Edition)
Python version with curses interface, logging, and system setup utilities.
"""

import curses
import os
import subprocess
import logging
import time
import shutil
import socket


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
    getattr(logging, level if level in logging._nameToLevel else "info")(msg)


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


def run_script(script_name: str):
    """Runs a script from the ./scripts directory."""
    path = os.path.join("scripts", script_name)
    if not os.path.isfile(path):
        log_and_print(f"Script not found: {path}", "error")
        return
    log_and_print(f"Running {script_name}...", "info")
    subprocess.run(["bash", path], check=False)
    log_and_print(f"{script_name} finished.", "success")


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
    current_row = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        title = "🛠️  MintyForge Menu"
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(1, width // 2 - len(title) // 2, title)
        stdscr.attroff(curses.color_pair(2))

        for idx, row in enumerate(MENU_OPTIONS):
            x = width // 2 - len(row) // 2
            y = 3 + idx
            if idx == current_row:
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
                time.sleep(1)
                break
            else:
                stdscr.clear()
                stdscr.addstr(2, 2, f"Running: {MENU_OPTIONS[current_row]} ...")
                stdscr.refresh()
                match current_row:
                    case 0: run_script("apt_install")
                    case 1: run_script("apt_remove")
                    case 2: run_script("flatpak_install")
                    case 3: run_script("themes_install")
                    case 4: run_script("drivers")
                    case 5: run_script("qt_install")
                    case 6: run_script("distroscript")
                stdscr.addstr(4, 2, "Press any key to return to menu...")
                stdscr.refresh()
                stdscr.getch()


def main():
    """Main entry point."""
    if not check_internet_connection():
        exit(1)
    disable_suspend_and_screensaver()
    update_system()

    # Setup curses colors
    curses.wrapper(init_curses)


def init_curses(stdscr):
    """Initialize curses color pairs and start the menu."""
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses_menu(stdscr)


if __name__ == "__main__":
    main()
