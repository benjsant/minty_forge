#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Interactive APT Remover
-------------------------------------
Provides a curses-based interface to remove unwanted APT packages.
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

# --- Core removal logic ---

def remove_single_package(pkg: dict):
    """Remove a single package by name."""
    name = pkg.get("name")
    desc = pkg.get("description", "")

    if not name:
        warn("Empty package name, skipping.")
        return

    info(f"Checking {name}...")
    if subprocess.run(f"dpkg -s {name} >/dev/null 2>&1", shell=True).returncode == 0:
        info(f"Removing {name} - {desc}")
        if run_cmd(f"sudo apt purge -y {name}"):
            success(f"{name} removed successfully.")
        else:
            warn(f"Failed to remove {name}.")
    else:
        warn(f"{name} is not installed, skipping.")

def remove_all_packages(packages: list[dict]):
    """Remove all unwanted packages from the list."""
    info("Starting removal of all unwanted packages...")

    for pkg in packages:
        name = pkg.get("name")
        desc = pkg.get("description", "")
        if not name:
            continue

        info(f"Removing {name} ({desc})...")
        if run_cmd(f"sudo apt purge -y {name}"):
            success(f"{name} removed successfully.")
        else:
            warn(f"Failed to remove {name}.")

    info("Running autoremove to clean dependencies...")
    run_cmd("sudo apt autoremove -y")

    success("✅ All unwanted packages removed successfully.")

# --- Curses menu ---

def curses_menu(stdscr, packages: list[dict]):
    """Display an interactive curses menu for package removal."""
    curses.curs_set(0)
    stdscr.nodelay(False)
    current_row = 0

    # Add "Remove All" at the top
    menu_items = [{"name": "__ALL__", "description": "Remove ALL unwanted packages"}] + packages

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "MintyForge - APT Remover", curses.A_BOLD)
        stdscr.addstr(1, 0, "Navigate with ↑/↓ | ENTER to remove | q to quit")
        stdscr.addstr(2, 0, "─" * 80)

        for idx, item in enumerate(menu_items):
            name = item["name"]
            desc = item["description"]
            label = f"👉 {desc}" if name == "__ALL__" else f"{name} - {desc}"

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
            stdscr.addstr(0, 0, f"Selected: {selected['description']}\n", curses.A_BOLD)
            stdscr.refresh()

            curses.endwin()  # leave curses mode for subprocess
            if selected["name"] == "__ALL__":
                remove_all_packages(packages)
            else:
                remove_single_package(selected)
            input("\nPress ENTER to return to menu...")
            curses.wrapper(lambda s: curses_menu(s, packages))
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

    packages = data.get("packages", [])
    if not packages:
        warn("No packages found in config.")
        return

    info("Launching MintyForge APT Remover...")
    curses.wrapper(lambda s: curses_menu(s, packages))

if __name__ == "__main__":
    main()
