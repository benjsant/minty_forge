#!/usr/bin/env python3
"""
MintyForge – Theme Installer (Curses Edition)
Replaces Bash 'themes_install', integrates with minty_forge.py
"""

import os
import json
import curses
import subprocess
import logging
from pathlib import Path

# ---------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "mintyforge.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def log_info(msg): print(f"[INFO] {msg}"); logging.info(msg)
def log_success(msg): print(f"[OK] {msg}"); logging.info(msg)
def log_warn(msg): print(f"[WARN] {msg}"); logging.warning(msg)
def log_error(msg): print(f"[ERROR] {msg}"); logging.error(msg)


# ---------------------------------------------------------------------
# User detection & paths
# ---------------------------------------------------------------------
USER_NAME = os.getenv("SUDO_USER") or os.getenv("USER")
USER_HOME = str(Path(f"~{USER_NAME}").expanduser())

if not USER_NAME:
    log_error("Unable to detect user.")
    exit(1)
else:
    log_info(f"Detected user: {USER_NAME} ({USER_HOME})")

CONFIG_DIR = "./configs"
THEMES_DIR = "./themes"
ICONS_DIR = "./icons"
CURSORS_DIR = "./cursors"

os.makedirs(THEMES_DIR, exist_ok=True)
os.makedirs(ICONS_DIR, exist_ok=True)
os.makedirs(CURSORS_DIR, exist_ok=True)

# ---------------------------------------------------------------------
# JSON loader
# ---------------------------------------------------------------------
def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)["themes"]
    except Exception as e:
        log_error(f"Failed to load {file_path}: {e}")
        exit(1)

themes_data = load_json(os.path.join(CONFIG_DIR, "theme.json"))
icons_data = load_json(os.path.join(CONFIG_DIR, "icons.json"))
cursors_data = load_json(os.path.join(CONFIG_DIR, "cursors.json"))


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------
def run_cmd(cmd, cwd=None, as_root=False):
    """Execute a shell command."""
    try:
        cmd_full = ["sudo", "bash", "-c", cmd] if as_root else ["bash", "-c", cmd]
        subprocess.run(cmd_full, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {cmd}\n{e}")
        exit(1)


def install_theme(theme, target_dir):
    """Clone and install a theme."""
    name = theme["name"]
    url = theme.get("url", "")
    cmd_user = theme.get("cmd_user", "")
    cmd_root = theme.get("cmd_root", "")

    log_info(f"Installing {name}...")

    # Clone repo
    if url and not os.path.isdir(target_dir):
        log_info(f"Cloning {url} into {target_dir}")
        subprocess.run(["git", "clone", "--depth=1", url, target_dir], check=False)
    elif os.path.isdir(target_dir):
        log_warn(f"{target_dir} already exists, skipping clone.")
    else:
        log_warn(f"No URL for {name}, skipping clone.")

    subprocess.run(["sudo", "chown", "-R", f"{USER_NAME}:{USER_NAME}", target_dir], check=False)

    # Run commands
    if cmd_user:
        log_info(f"Running user command for {name}")
        run_cmd(cmd_user, cwd=target_dir, as_root=False)
    if cmd_root:
        log_info(f"Running root command for {name}")
        run_cmd(cmd_root, cwd=target_dir, as_root=True)

    log_success(f"Installation completed for {name}.")


def apply_gsettings(schema, key, value):
    log_info(f"Applying {key} → {value}")
    try:
        subprocess.run(
            ["sudo", "-u", USER_NAME, "gsettings", "set", schema, key, value],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to apply {key}: {e}")


def verify_gsettings(schema, key, expected):
    result = subprocess.run(
        ["sudo", "-u", USER_NAME, "gsettings", "get", schema, key],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    current = result.stdout.strip().replace("'", "")
    if current == expected:
        log_success(f"Verified: {key} = {expected}")
    else:
        log_warn(f"Expected {expected}, got {current}")


# ---------------------------------------------------------------------
# Curses menu for theme selection
# ---------------------------------------------------------------------
def select_theme(stdscr, themes, category):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)

    selected_idx = 0
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        title = f"Select {category} Theme"
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(1, w // 2 - len(title) // 2, title)
        stdscr.attroff(curses.color_pair(2))

        for idx, theme in enumerate(themes):
            line = f"{theme['name']} — {theme['description']}"
            x = w // 2 - len(line) // 2
            y = 3 + idx
            if idx == selected_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, line)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, line)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and selected_idx > 0:
            selected_idx -= 1
        elif key == curses.KEY_DOWN and selected_idx < len(themes) - 1:
            selected_idx += 1
        elif key in [10, 13]:  # Enter key
            return themes[selected_idx]


# ---------------------------------------------------------------------
# Main process
# ---------------------------------------------------------------------
def run_curses_installer(stdscr):
    stdscr.clear()
    gtk = select_theme(stdscr, themes_data, "GTK")
    icon = select_theme(stdscr, icons_data, "Icon")
    cursor = select_theme(stdscr, cursors_data, "Cursor")

    stdscr.clear()
    stdscr.addstr(2, 2, f"Installing themes...")
    stdscr.refresh()

    install_theme(gtk, f"{THEMES_DIR}/{gtk['name_to_use']}")
    install_theme(icon, f"{ICONS_DIR}/{icon['name_to_use']}")
    install_theme(cursor, f"{CURSORS_DIR}/{cursor['name_to_use']}")

    apply_gsettings("org.cinnamon.desktop.interface", "gtk-theme", gtk["name_to_use"])
    apply_gsettings("org.cinnamon.desktop.interface", "icon-theme", icon["name_to_use"])
    apply_gsettings("org.cinnamon.desktop.interface", "cursor-theme", cursor["name_to_use"])
    apply_gsettings("org.cinnamon.desktop.wm.preferences", "theme", gtk["name_to_use"])

    verify_gsettings("org.cinnamon.desktop.interface", "gtk-theme", gtk["name_to_use"])
    verify_gsettings("org.cinnamon.desktop.interface", "icon-theme", icon["name_to_use"])
    verify_gsettings("org.cinnamon.desktop.interface", "cursor-theme", cursor["name_to_use"])
    verify_gsettings("org.cinnamon.desktop.wm.preferences", "theme", gtk["name_to_use"])

    stdscr.addstr(8, 2, "🎉 Theme installation completed successfully!")
    stdscr.addstr(10, 2, "Press any key to exit...")
    stdscr.refresh()
    stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(run_curses_installer)
