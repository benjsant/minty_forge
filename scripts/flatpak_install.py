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

CONFIG_FILE = Path("configs/flatpak.json")

# --- Colorized output ---
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
BLUE = "\033[1;34m"
RESET = "\033[0m"

def info(msg: str): print(f"{BLUE}[INFO]{RESET} {msg}")
def success(msg: str): print(f"{GREEN}[OK]{RESET} {msg}")
def warn(msg: str): print(f"{YELLOW}[WARN]{RESET} {msg}")
def error(msg: str): print(f"{RED}[ERROR]{RESET} {msg}")


# --- Utility commands ---
def run_cmd(cmd: str) -> bool:
    """Run a shell command and return True if successful."""
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        error(f"Command failed: {cmd}\n{e}")
        return False
    except KeyboardInterrupt:
        warn("Operation cancelled by user.")
        return False


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
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    current_row = 0
    menu_items = [{"app": "__ALL__", "description": "Install ALL Flatpaks"}] + flatpaks

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(0, 0, "MintyForge - Flatpak Installer")
        stdscr.attroff(curses.color_pair(2))
        stdscr.addstr(1, 0, "Navigate ↑/↓ | ENTER to install | q to quit")
        stdscr.addstr(2, 0, "─" * (width - 1))

        for idx, item in enumerate(menu_items):
            app = item.get("app")
            desc = item.get("description", "")
            label = f"👉 {desc}" if app == "__ALL__" else f"{app} - {desc}"

            if idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx + 4, 2, label[:width - 4])
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(idx + 4, 2, label[:width - 4])

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
            current_row += 1
        elif key in (10, 13):  # ENTER
            return menu_items[current_row]
        elif key in [ord("q"), ord("Q")]:
            return None


# --- Main loop ---
def main():
    if not CONFIG_FILE.exists():
        error(f"{CONFIG_FILE} not found.")
        return

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        error(f"Invalid JSON in {CONFIG_FILE}: {e}")
        return

    flatpaks = data.get("flatpaks", [])
    if not flatpaks:
        warn("No Flatpaks found in config.")
        return

    info("Launching MintyForge Flatpak Installer...")

    while True:
        try:
            selected = curses.wrapper(lambda s: curses_menu(s, flatpaks))
        except curses.error:
            error("Curses display error encountered.")
            break

        if not selected:
            break

        os.system("clear")
        print(f"\n=== Installing: {selected.get('description', selected.get('app'))} ===\n")

        if selected["app"] == "__ALL__":
            install_all_flatpaks(flatpaks)
        else:
            install_single_flatpak(selected)

        try:
            input("\nPress ENTER to return to the menu...")
        except KeyboardInterrupt:
            warn("Returning to menu...")

        os.system("clear")

    success("Finished executing flatpak_install.")


if __name__ == "__main__":
    main()
