#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - External Packages Installer
---------------------------------------
Installs external packages (not from standard APT) like Distrobox or VirtualBox Oracle.
Uses curses menu to select packages and execute installation commands.
"""

import os
import json
import curses
import subprocess
from pathlib import Path

CONFIG_FILE = Path("configs/external_packages.json")

# --- Terminal Colors ---
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
    """Execute shell command, return True if successful."""
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        error(f"Command failed: {cmd}\n{e}")
        return False

# --- Core logic ---
def install_package(pkg: dict):
    """Run the installation command for an external package."""
    name = pkg.get("name")
    desc = pkg.get("description", "")
    cmd = pkg.get("cmd")

    if not cmd:
        warn(f"No command defined for {name}, skipping.")
        return

    info(f"Installing {name} - {desc}...")
    if run_cmd(cmd):
        success(f"{name} installed successfully.")
    else:
        warn(f"Failed to install {name}.")

def curses_menu(stdscr, packages: list[dict]):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    current_row = 0
    menu_items = [{"name": "__ALL__", "description": "Install ALL packages"}] + packages

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        max_visible = height - 6
        start_index = max(0, min(current_row - max_visible + 1, len(menu_items) - max_visible))
        visible_items = menu_items[start_index:start_index + max_visible]

        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(0, 0, "MintyForge - External Packages Installer")
        stdscr.attroff(curses.color_pair(2))
        stdscr.addstr(1, 0, "Navigate ↑/↓ | ENTER to install | q to quit")
        stdscr.addstr(2, 0, "─" * (width - 1))

        for idx, item in enumerate(visible_items):
            name = item.get("name", "Unknown")
            desc = item.get("description", "")
            label = f"👉 {desc}" if name == "__ALL__" else f"{name} - {desc}"
            label = label[:width-4]
            row_index = idx + 4
            if start_index + idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(row_index, 2, label)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(row_index, 2, label)

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
            current_row += 1
        elif key in (10, 13):  # Enter
            selected = menu_items[current_row]
            curses.endwin()
            os.system("clear")
            print(f"\n=== Installing: {selected.get('description', selected.get('name'))} ===\n")

            if selected["name"] == "__ALL__":
                for pkg in packages:
                    install_package(pkg)
            else:
                install_package(selected)

            input("\nPress ENTER to return to the menu...")
            curses.wrapper(lambda s: curses_menu(s, packages))
            return
        elif key in [ord("q"), ord("Q")]:
            break
        stdscr.refresh()

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
        warn("No external packages found.")
        return

    info("Launching MintyForge External Packages Installer...")
    curses.wrapper(lambda s: curses_menu(s, packages))

if __name__ == "__main__":
    main()
