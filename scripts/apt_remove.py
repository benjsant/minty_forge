#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Interactive APT Remover (stable curses version)
------------------------------------------------------------
Curses-based interface to remove unwanted APT packages.
Includes an option to remove all listed packages at once.

Usage:
    python3 apt_remove.py
"""

import os
import json
import curses
import subprocess
from pathlib import Path

# --- Configuration paths ---
CONFIG_FILE = Path("configs/remove.json")

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
        warn("Operation cancelled by user.")
        return False

def is_package_installed(name: str) -> bool:
    """Check if a package is installed."""
    result = subprocess.run(
        f"dpkg -l | grep -E '^ii' | grep -qw {name}",
        shell=True
    )
    return result.returncode == 0

def remove_single_package(pkg: dict):
    """Remove a single package."""
    name = pkg.get("name")
    desc = pkg.get("description", "")
    if not name:
        warn("Empty package name, skipping.")
        return

    info(f"Checking {name}...")
    if is_package_installed(name):
        info(f"Removing {name} ({desc})...")
        if run_cmd(f"sudo apt purge -y {name}"):
            success(f"{name} removed successfully.")
        else:
            warn(f"Failed to remove {name}.")
    else:
        warn(f"{name} not installed, skipping.")

def remove_all_packages(packages: list[dict]):
    """Remove all packages from the config."""
    info("Removing all unwanted packages...")
    for pkg in packages:
        name = pkg.get("name")
        if not name:
            continue
        run_cmd(f"sudo apt purge -y {name}")
    run_cmd("sudo apt autoremove -y")
    success("✅ All unwanted packages removed successfully.")

# --- Curses Menu ---

def curses_menu(stdscr, packages: list[dict]):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    current_row = 0
    menu_items = [{"name": "__ALL__", "description": "Remove ALL unwanted packages"}] + packages

    while True:
        stdscr.clear()
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(0, 0, "MintyForge - APT Remover")
        stdscr.attroff(curses.color_pair(2))
        stdscr.addstr(1, 0, "Navigate ↑/↓ | ENTER to remove | q to quit")
        stdscr.addstr(2, 0, "─" * 80)

        for idx, item in enumerate(menu_items):
            name = item.get("name", "Unknown")
            desc = item.get("description", "")
            label = f"👉 {desc}" if name == "__ALL__" else f"{name} - {desc}"

            if idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx + 4, 2, label)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(idx + 4, 2, label)

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
            current_row += 1
        elif key in (10, 13):  # Enter
            selected = menu_items[current_row]
            # Quit curses before executing commands
            curses.endwin()
            os.system("clear")
            print(f"\n=== Removing: {selected.get('description', selected.get('name'))} ===\n")

            if selected["name"] == "__ALL__":
                remove_all_packages(packages)
            else:
                remove_single_package(selected)

            print("\nPress ENTER to return to the menu...")
            input()
            os.system("clear")

            # relancer le menu sans réinitialiser curses.wrapper
            curses.curs_set(0)
            stdscr.clear()
            continue
        elif key in [ord("q"), ord("Q")]:
            break

        stdscr.refresh()

# --- Main ---

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

    info("Launching MintyForge APT Remover...")
    curses.wrapper(lambda s: curses_menu(s, packages))
    success("MintyForge APT Remover exited cleanly.")

if __name__ == "__main__":
    main()
