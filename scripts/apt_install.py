#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Interactive APT Installer (safe curses version)
-------------------------------------------------------------
Provides a curses-based menu to install APT packages individually or all at once,
with robust handling for terminal height and width.
"""

import os
import json
import curses
import subprocess
from pathlib import Path

# --- Configuration paths ---
CONFIG_FILE = Path("configs/install.json")

# --- Colorized terminal output ---
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
BLUE = "\033[1;34m"
RESET = "\033[0m"

def info(msg: str): print(f"{BLUE}[INFO]{RESET} {msg}")
def success(msg: str): print(f"{GREEN}[OK]{RESET} {msg}")
def warn(msg: str): print(f"{YELLOW}[WARN]{RESET} {msg}")
def error(msg: str): print(f"{RED}[ERROR]{RESET} {msg}")

def run_cmd(cmd: str) -> bool:
    """Run a shell command and return True if successful."""
    try:
        result = subprocess.run(cmd, shell=True)
        return result.returncode == 0
    except KeyboardInterrupt:
        warn("Installation interrupted by user.")
        return False

# --- Core installation logic ---

def install_single_package(pkg: dict):
    """Install one package by name."""
    name = pkg.get("name")
    desc = pkg.get("description", "")

    if not name:
        warn("Empty package name, skipping.")
        return

    info(f"Checking {name}...")
    if subprocess.run(f"dpkg -l | grep -q '^ii  {name}'", shell=True).returncode == 0:
        warn(f"{name} is already installed, skipping.")
        return

    info(f"Installing {name} - {desc}")
    if run_cmd(f"sudo apt install -y {name}"):
        success(f"{name} installed successfully.")
    else:
        warn(f"Failed to install {name}.")

def install_all_packages(packages: list[dict]):
    """Install all packages from the list."""
    info("Starting installation of all packages...")

    for pkg in packages:
        name = pkg.get("name")
        desc = pkg.get("description", "")
        if not name:
            continue

        info(f"Installing {name} ({desc})...")
        if run_cmd(f"sudo apt install -y {name}"):
            success(f"{name} installed successfully.")
        else:
            warn(f"Failed to install {name}.")

    success("✅ All packages processed.")

# --- Safe curses menu ---

def curses_menu(stdscr, packages: list[dict]):
    """Display an interactive curses menu for package installation."""
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    current_row = 0
    menu_items = [{"name": "__ALL__", "description": "Install ALL packages"}] + packages

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Safety: handle small terminals gracefully
        if height < 10 or width < 40:
            stdscr.addstr(0, 0, "Please enlarge your terminal (min 40x10).")
            stdscr.refresh()
            curses.napms(1500)
            continue

        max_visible = height - 6
        start_index = max(0, min(current_row - max_visible + 1, len(menu_items) - max_visible))
        visible_items = menu_items[start_index:start_index + max_visible]

        # Header
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(0, 0, "MintyForge - APT Installer".center(width - 1))
        stdscr.attroff(curses.color_pair(2))
        stdscr.addstr(1, 0, "Navigate ↑/↓ | ENTER to install | q to quit".center(width - 1))
        stdscr.addstr(2, 0, "─" * (width - 1))

        # List display
        for idx, item in enumerate(visible_items):
            name = item.get("name", "Unknown")
            desc = item.get("description", "")
            label = f"[ALL] {desc}" if name == "__ALL__" else f"{name} - {desc}"
            label = label[:width - 4]

            row_index = idx + 4
            if start_index + idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(row_index, 2, label)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(row_index, 2, label)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
            current_row += 1
        elif key in (10, 13):  # Enter
            return menu_items[current_row]
        elif key in [ord("q"), ord("Q")]:
            return None

# --- Main entrypoint ---

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

    packages = data.get("packages", [])
    if not packages:
        warn("No packages found in config.")
        return

    info("Launching MintyForge APT Installer...")

    while True:
        selected = curses.wrapper(lambda s: curses_menu(s, packages))
        if not selected:
            break  # Quit

        os.system("clear")
        print(f"\n=== Installing: {selected.get('description', selected.get('name'))} ===\n")

        if selected["name"] == "__ALL__":
            install_all_packages(packages)
        else:
            install_single_package(selected)

        input("\nPress ENTER to return to the menu...")

if __name__ == "__main__":
    main()
