#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge – Main Script (Cross-DE Edition)
-------------------------------------------
Main interactive curses menu for Linux Mint and compatible DEs.
Handles APT package installation, theme setup, Flatpak management, and driver configuration.
Disables sleep/screensaver during setup via systemd-logind (dbus-send),
then restores normal settings at shutdown.
"""

import curses
import os
import subprocess
import logging
import time
import socket
from pathlib import Path
import tempfile

# ---------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "mintyforge.log")
INHIBIT_FD_FILE = Path(tempfile.gettempdir()) / "mintyforge_inhibit_fd"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def log_and_print(msg: str, level: str = "info"):
    """Log and print a message with color level prefix."""
    colors = {
        "info": "\033[1;34m",
        "success": "\033[1;32m",
        "warn": "\033[1;33m",
        "error": "\033[1;31m",
    }
    prefix = {
        "info": "[INFO]",
        "success": "[OK]",
        "warn": "[WARN]",
        "error": "[ERROR]",
    }.get(level, "[INFO]")

    color = colors.get(level, "")
    reset = "\033[0m"
    print(f"{color}{prefix}{reset} {msg}")
    getattr(logging, level if level in logging._nameToLevel else "info")(msg)


def check_internet_connection(host="archive.ubuntu.com", port=80, timeout=2):
    """Check internet connectivity."""
    try:
        socket.create_connection((host, port), timeout=timeout)
        log_and_print("Internet connection detected.", "success")
        return True
    except OSError:
        log_and_print("No Internet connection detected. Please connect and retry.", "error")
        return False


def disable_suspend_and_screensaver():
    """Disable suspend/screensaver temporarily via D-Bus or Cinnamon fallback."""
    log_and_print("Attempting to inhibit suspend and screensaver...", "info")
    os.environ["PATH"] += os.pathsep + "/usr/bin"

    inhibit_cmd = [
        "/usr/bin/dbus-send",
        "--system",
        "--dest=org.freedesktop.login1",
        "--type=method_call",
        "--print-reply",
        "/org/freedesktop/login1",
        "org.freedesktop.login1.Manager.Inhibit",
        "string:sleep:idle",
        "string:MintyForge",
        "string:System setup in progress",
        "string:block"
    ]

    try:
        subprocess.run(inhibit_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log_and_print("System sleep and idle inhibited via D-Bus (systemd-logind).", "success")
        return
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        log_and_print(f"D-Bus inhibition failed: {e}. Falling back to Cinnamon.", "warn")

    # Cinnamon fallback
    fallback_cmds = [
        ["gsettings", "set", "org.cinnamon.settings-daemon.plugins.power", "sleep-inactive-ac-timeout", "0"],
        ["gsettings", "set", "org.cinnamon.settings-daemon.plugins.power", "sleep-inactive-battery-timeout", "0"],
        ["gsettings", "set", "org.cinnamon.desktop.screensaver", "lock-enabled", "false"],
    ]
    for cmd in fallback_cmds:
        subprocess.run(cmd, check=False)
    log_and_print("Fallback applied: suspend and screensaver disabled via gsettings.", "success")


def restore_power_settings():
    """Restore default Cinnamon power and lock settings."""
    log_and_print("Restoring Cinnamon power settings...", "info")
    cmds = [
        ["gsettings", "set", "org.cinnamon.settings-daemon.plugins.power", "sleep-inactive-ac-timeout", "1200"],
        ["gsettings", "set", "org.cinnamon.settings-daemon.plugins.power", "sleep-inactive-battery-timeout", "900"],
        ["gsettings", "set", "org.cinnamon.desktop.screensaver", "lock-enabled", "true"],
    ]
    for cmd in cmds:
        subprocess.run(cmd, check=False)
    log_and_print("Power and screensaver settings restored.", "success")


def update_system():
    """Update system packages (APT)."""
    log_and_print("Updating APT packages...", "info")
    subprocess.run(["sudo", "apt", "update", "-y"], check=False)
    subprocess.run(["sudo", "apt", "upgrade", "-y"], check=False)
    log_and_print("System packages updated successfully.", "success")


def update_flatpaks():
    """Update installed Flatpaks automatically at startup."""
    log_and_print("Checking for Flatpak updates...", "info")
    try:
        result = subprocess.run(["flatpak", "update", "-y"], check=False, capture_output=True, text=True)
        if "Nothing to do" in result.stdout:
            log_and_print("No Flatpak updates available.", "info")
        else:
            log_and_print("Flatpaks updated successfully.", "success")
    except FileNotFoundError:
        log_and_print("Flatpak not installed — skipping Flatpak updates.", "warn")


def pause_message():
    """Pause before returning to menu."""
    print("\nPress ENTER to return to MintyForge menu...")
    try:
        os.system("read -r _")
    except Exception:
        time.sleep(1)


# ---------------------------------------------------------------------
# Script execution system
# ---------------------------------------------------------------------
SCRIPTS_DIR = Path("scripts")
ROOT = Path(".").resolve()

def find_script(script_name: str):
    """Locate script path."""
    candidates = [
        SCRIPTS_DIR / f"{script_name}.py",
        SCRIPTS_DIR / script_name,
        ROOT / f"{script_name}.py",
        ROOT / script_name,
    ]
    return next((p for p in candidates if p.exists()), None)


def run_script(script_name: str):
    """Run a script by name, with safety and logs."""
    path = find_script(script_name)
    if not path:
        log_and_print(f"Script not found: {script_name}", "error")
        pause_message()
        return

    log_and_print(f"Running {path}...", "info")
    curses.endwin()

    try:
        if path.suffix == ".py":
            subprocess.run(["python3", str(path)], check=False)
        elif os.access(str(path), os.X_OK):
            subprocess.run([str(path)], check=False)
        else:
            subprocess.run(["bash", str(path)], check=False)
        log_and_print(f"Finished executing {script_name}.", "success")
    except Exception as e:
        log_and_print(f"Error running {path}: {e}", "error")

    pause_message()


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
# Curses Menu UI
# ---------------------------------------------------------------------
def curses_menu(stdscr):
    """Display the MintyForge curses main menu."""
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
        elif key in [10, 13]:  # ENTER
            if current_row == len(MENU_OPTIONS) - 1:  # Exit
                restore_power_settings()
                log_and_print("Exiting MintyForge. Goodbye!", "success")
                time.sleep(0.5)
                break
            else:
                script_name = SCRIPT_MAPPING.get(current_row)
                if script_name:
                    run_script(script_name)
                else:
                    log_and_print("No script mapped to this option.", "warn")
        elif key in [ord("q"), ord("Q")]:
            restore_power_settings()
            log_and_print("Exiting MintyForge. Goodbye!", "success")
            break


# ---------------------------------------------------------------------
# Main Entrypoint
# ---------------------------------------------------------------------
def main():
    """MintyForge main entrypoint."""
    if not check_internet_connection():
        return

    disable_suspend_and_screensaver()
    update_system()
    update_flatpaks()  # ✅ automatic flatpak update

    try:
        curses.wrapper(curses_menu)
    finally:
        restore_power_settings()
        log_and_print("MintyForge shutdown completed — system settings restored.", "success")


if __name__ == "__main__":
    main()
