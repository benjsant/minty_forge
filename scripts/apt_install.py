#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Interactive APT Installer (safe curses version)
-------------------------------------------------------------
Provides a curses-based menu to install APT packages individually or all at once,
with robust handling for terminal height and width.

Security: Uses secure subprocess calls without shell=True
"""

import os
import sys
import curses
from pathlib import Path

# Add parent directory to path for utils import
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    check_package_installed, apt_install,
    info, success, warn, error,
    load_package_list
)

# --- Configuration paths ---
CONFIG_FILE = Path("configs/install.json")

# --- Core installation logic ---

def install_single_package(pkg: dict):
    """Install one package by name."""
    name = pkg.get("name")
    desc = pkg.get("description", "")

    if not name:
        warn("Empty package name, skipping.")
        return

    info(f"Checking {name}...")
    if check_package_installed(name):
        warn(f"{name} is already installed, skipping.")
        return

    info(f"Installing {name} - {desc}")
    result = apt_install([name])
    if result.success:
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
        result = apt_install([name])
        if result.success:
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
        packages = load_package_list(CONFIG_FILE)  # Now with validation!
    except Exception as e:
        error(f"Failed to load config: {e}")
        return

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
