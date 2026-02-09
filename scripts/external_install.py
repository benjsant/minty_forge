#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - External Packages Installer
---------------------------------------
Installs external packages (not from standard APT) like Distrobox or VirtualBox Oracle.
Uses curses menu to select packages and execute installation commands.

Security Note: External package commands from JSON are executed via bash.
Ensure external_packages.json is trusted and not editable by untrusted users.
"""

import os
import sys
import json
import curses
from pathlib import Path

# Add parent directory to path for utils import
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    run_command,
    info, success, warn, error,
    load_package_list
)

CONFIG_FILE = Path("configs/external_packages.json")


def install_package(pkg: dict):
    """Run the installation command for an external package.
    
    Security: Commands are from trusted JSON config file.
    Uses bash to execute complex shell commands (pipes, redirections, etc.).
    """
    name = pkg.get("name")
    desc = pkg.get("description", "")
    cmd = pkg.get("cmd")

    if not cmd:
        warn(f"No command defined for {name}, skipping.")
        return

    info(f"Installing {name} - {desc}...")
    # External commands can be complex, use bash safely
    result = run_command(["bash", "-c", cmd])
    if result.success:
        success(f"{name} installed successfully.")
    else:
        warn(f"Failed to install {name}.")


def curses_menu(stdscr, packages: list[dict]):
    """Display the curses-based selection menu."""
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
        elif key in (10, 13):  # ENTER key
            selected = menu_items[current_row]
            stdscr.clear()
            stdscr.refresh()
            # On sort du menu pour exécuter l’installation
            return selected
        elif key in [ord("q"), ord("Q")]:
            return None


def main():
    """Main entry point."""
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

    while True:
        selected = curses.wrapper(lambda s: curses_menu(s, packages))
        if not selected:
            break  # Quit
        os.system("clear")

        print(f"\n=== Installing: {selected.get('description', selected.get('name'))} ===\n")

        if selected["name"] == "__ALL__":
            for pkg in packages:
                install_package(pkg)
        else:
            install_package(selected)

        input("\nPress ENTER to return to the menu...")

    success("Finished executing external_install.")


if __name__ == "__main__":
    main()
