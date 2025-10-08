#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Interactive Flatpak Installer
------------------------------------------
Provides a curses-based interface to install Flatpaks.
Includes an option to install all Flatpaks at once.

Usage:
    python3 flatpak_install.py
"""

import os
import json
import curses
import subprocess
from pathlib import Path

# --- Configuration paths ---
CONFIG_FILE = Path("configs/flatpak.json")

# --- Colorized terminal output ---
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
BLUE = "\033[1;34m"
RESET = "\033[0m"

def info(msg: str):
    print(f"{BLUE}[INFO]{RESET} {msg}")

def success(msg: str):
    print(f"{GREEN}[OK]{RESET} {msg}")

def warn(msg: str):
    print(f"{YELLOW}[WARN]{RESET} {msg}")

def error(msg: str):
    print(f"{RED}[ERROR]{RESET} {msg}")

def run_cmd(cmd: str) -> bool:
    """Run a shell command and return True if successful."""
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

# --- Core logic ---

def is_flatpak_installed(app_id: str) -> bool:
    """Check if a Flatpak app is already installed."""
    result = subprocess.run(
        f"flatpak list | grep -F {app_id}",
        shell=True,
        stdout=subprocess.DEVNULL
    )
    return result.returncode == 0

def install_single_flatpak(flatpak: dict):
    """Install a single Flatpak app."""
    app = flatpak.get("app")
    source = flatpak.get("source", "flathub")
    desc = flatpak.get("description", "")

    if not app:
        warn("Empty Flatpak ID, skipping.")
        return

    if is_flatpak_installed(app):
        warn(f"{app} is already installed, skipping.")
        return

    info(f"Installing {app} - {desc} from {source}...")
    if run_cmd(f"flatpak install -y {source} {app}"):
        success(f"{app} installed successfully.")
    else:
        warn(f"Failed to install {app}.")

def install_all_flatpaks(flatpaks: list[dict]):
    """Install all Flatpaks from the list."""
    info("Starting installation of all Flatpaks...")

    for flatpak in flatpaks:
        install_single_flatpak(flatpak)

    success("✅ All Flatpaks installed successfully.")

# --- Curses menu ---

def curses_menu(stdscr, flatpaks: list[dict]):
    curses.curs_set(0)
    stdscr.nodelay(False)
    current_row = 0

    # Add "Install All" at the top
    menu_items = [{"app": "__ALL__", "description": "Install ALL Flatpaks"}] + flatpaks

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "MintyForge - Flatpak Installer", curses.A_BOLD)
        stdscr.addstr(1, 0, "Navigate with ↑/↓ | ENTER to install | q to quit")
        stdscr.addstr(2, 0, "─" * 80)

        for idx, item in enumerate(menu_items):
            app = item.get("app")
            desc = item.get("description", "")
            label = f"👉 {desc}" if app == "__ALL__" else f"{app} - {desc}"

            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(idx + 4, 2, label)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 4, 2, label)

        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
            current_row += 1
        elif key == ord("\n"):
            stdscr.clear()
            selected = menu_items[current_row]
            stdscr.addstr(0, 0, f"Selected: {selected.get('description','')}\n", curses.A_BOLD)
            stdscr.refresh()

            curses.endwin()  # leave curses mode for subprocess
            if selected.get("app") == "__ALL__":
                install_all_flatpaks(flatpaks)
            else:
                install_single_flatpak(selected)
            input("\nPress ENTER to return to menu...")
            curses.wrapper(lambda s: curses_menu(s, flatpaks))
            break
        elif key in [ord("q"), ord("Q")]:
            break

        stdscr.refresh()

# --- Main entrypoint ---

def main():
    if not CONFIG_FILE.exists():
        error(f"{CONFIG_FILE} not found.")
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    flatpaks = data.get("flatpaks", [])
    if not flatpaks:
        warn("No Flatpaks found in config.")
        return

    info("Launching MintyForge Flatpak Installer...")
    curses.wrapper(lambda s: curses_menu(s, flatpaks))

if __name__ == "__main__":
    main()
