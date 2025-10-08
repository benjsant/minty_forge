#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Qt Theme Installer (Python version)
------------------------------------------------
Interactive installer and configurator for Qt theming.
Supports Kvantum theme downloads and configuration via curses.
"""

import os
import json
import curses
import subprocess
from pathlib import Path

CONFIG_FILE = Path("configs/qt.json")
THEMES_DIR = Path.home() / ".themes_kvantum"

# ---------------------------------------------------------------------
# Colorful logging helpers
# ---------------------------------------------------------------------
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
BLUE = "\033[1;34m"
RESET = "\033[0m"

def info(msg: str): print(f"{BLUE}[INFO]{RESET} {msg}")
def success(msg: str): print(f"{GREEN}[OK]{RESET} {msg}")
def warn(msg: str): print(f"{YELLOW}[WARN]{RESET} {msg}")
def error(msg: str): print(f"{RED}[ERROR]{RESET} {msg}")

# ---------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------
def run_cmd(cmd: str) -> bool:
    """Run a system command and return True if successful."""
    return subprocess.run(cmd, shell=True).returncode == 0

def ensure_qt_tools():
    """Ensure Qt theming tools are installed."""
    info("Checking required Qt tools...")
    pkgs = ["qt5ct", "qt6ct", "qt5-style-kvantum", "kvantum-manager"]
    run_cmd("sudo apt update -y")
    run_cmd("sudo apt install -y " + " ".join(pkgs))
    success("Qt theming tools installed.")

def configure_environment():
    """Add QT environment variables to ~/.profile."""
    profile = Path.home() / ".profile"
    info("Configuring environment variables...")

    content = profile.read_text(encoding="utf-8") if profile.exists() else ""
    content = "\n".join(
        line for line in content.splitlines()
        if not line.startswith("# --- QT THEME CONFIGURATION (Minty Forge) ---")
        and not line.startswith("# --- END QT CONFIGURATION ---")
    )

    with open(profile, "w", encoding="utf-8") as f:
        f.write(content)
        f.write(
            "\n\n# --- QT THEME CONFIGURATION (Minty Forge) ---\n"
            "export QT_QPA_PLATFORMTHEME=qt5ct\n"
            "export QT_PLATFORMTHEME=qt5ct\n"
            "export QT_QPA_PLATFORMTHEME_QT6=qt6ct\n"
            "export QT_PLATFORMTHEME_QT6=qt6ct\n"
            "export QT_STYLE_OVERRIDE=kvantum\n"
            "# --- END QT CONFIGURATION ---\n"
        )

    success("Environment variables configured.")

def write_qt_conf(style: str = "kvantum"):
    """Write style configuration to qt5ct/qt6ct."""
    info(f"Writing qt5ct and qt6ct configuration for style={style}...")
    for conf in [".config/qt5ct/qt5ct.conf", ".config/qt6ct/qt6ct.conf"]:
        path = Path.home() / conf
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("[Appearance]\n")
            f.write(f"style={style}\n")
    success("Qt configuration updated.")

def download_kvantum_theme(theme: dict):
    """Download Kvantum themes if 'download' field exists."""
    theme_name = theme.get("theme")
    repo = theme.get("download")
    if not repo:
        warn(f"No download URL for {theme_name}, skipping.")
        return

    THEMES_DIR.mkdir(parents=True, exist_ok=True)
    dest = THEMES_DIR / theme_name
    if dest.exists():
        warn(f"Theme {theme_name} already downloaded.")
        return

    info(f"Downloading Kvantum theme {theme_name} from {repo}...")
    if run_cmd(f"git clone {repo} '{dest}'"):
        success(f"{theme_name} downloaded to {dest}.")
    else:
        error(f"Failed to download {theme_name}.")

def apply_theme(theme: dict):
    """Apply a single theme."""
    theme_name = theme.get("theme")
    if not theme_name:
        warn("Empty theme name, skipping.")
        return

    info(f"Applying Qt theme {theme_name}...")
    write_qt_conf(style="kvantum")

    # Apply user command if needed later (future-proof)
    success(f"{theme_name} applied successfully.")

# ---------------------------------------------------------------------
# curses menu
# ---------------------------------------------------------------------
def curses_menu(stdscr, themes: list[dict]):
    curses.curs_set(0)
    stdscr.nodelay(False)
    current_row = 0

    menu_items = [
        {"theme": "__ALL__", "description": "Apply ALL Qt themes"},
        {"theme": "__DOWNLOAD_ALL__", "description": "Download ALL Kvantum themes"}
    ] + themes

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "MintyForge - Qt Theme Installer", curses.A_BOLD)
        stdscr.addstr(1, 0, "Navigate with ↑/↓ | ENTER to apply | q to quit")
        stdscr.addstr(2, 0, "─" * 80)

        for idx, item in enumerate(menu_items):
            theme = item.get("theme")
            desc = item.get("description", "")
            label = f"👉 {desc}" if theme.startswith("__") else f"{theme} - {desc}"

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
            curses.endwin()
            selected = menu_items[current_row]
            theme_id = selected.get("theme")

            if theme_id == "__ALL__":
                for t in themes:
                    apply_theme(t)
            elif theme_id == "__DOWNLOAD_ALL__":
                for t in themes:
                    if "download" in t:
                        download_kvantum_theme(t)
            else:
                # Download if needed, then apply
                if "download" in selected:
                    download_kvantum_theme(selected)
                apply_theme(selected)

            input("\nPress ENTER to return to menu...")
            return
        elif key in [ord("q"), ord("Q")]:
            break

        stdscr.refresh()

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    if not CONFIG_FILE.exists():
        error(f"{CONFIG_FILE} not found.")
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        themes = json.load(f)

    if not themes:
        warn("No Qt themes found in config.")
        return

    info("Preparing Qt environment...")
    ensure_qt_tools()
    configure_environment()

    info("Launching MintyForge Qt Installer...")
    curses.wrapper(lambda s: curses_menu(s, themes))

if __name__ == "__main__":
    main()
