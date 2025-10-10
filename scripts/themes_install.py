#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge – Theme Installer (Curses Edition)
----------------------------------------------
Interactive desktop theming utility for Linux Mint Cinnamon.
Applies Cinnamon theme settings via dconf rather than gsettings,
and ensures Slick Greeter is configured properly.
"""

import os
import json
import curses
import subprocess
import shutil
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
# User detection
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

for d in [THEMES_DIR, ICONS_DIR, CURSORS_DIR]:
    os.makedirs(d, exist_ok=True)


# ---------------------------------------------------------------------
# Load JSON files
# ---------------------------------------------------------------------
def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)["themes"]
    except Exception as e:
        log_error(f"Failed to load {file_path}: {e}")
        exit(1)

themes_data = load_json(os.path.join(CONFIG_DIR, "themes_gtk.json"))
icons_data = load_json(os.path.join(CONFIG_DIR, "themes_icons.json"))
cursors_data = load_json(os.path.join(CONFIG_DIR, "themes_cursors.json"))


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------
def run_cmd(cmd, cwd=None, as_root=False):
    """Execute shell command safely."""
    try:
        full_cmd = ["sudo", "bash", "-c", cmd] if as_root else ["bash", "-c", cmd]
        subprocess.run(full_cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {cmd}\n{e}")
        exit(1)


def install_theme(theme, target_dir):
    """Clone and install theme with optional commands."""
    name = theme["name"]
    url = theme.get("url", "")
    cmd_user = theme.get("cmd_user", "")
    cmd_root = theme.get("cmd_root", "")

    log_info(f"Installing {name}...")

    if url and not os.path.isdir(target_dir):
        log_info(f"Cloning {url} into {target_dir}")
        subprocess.run(["git", "clone", "--depth=1", url, target_dir], check=False)
    else:
        log_warn(f"{target_dir} exists or no URL, skipping clone.")

    subprocess.run(["sudo", "chown", "-R", f"{USER_NAME}:{USER_NAME}", target_dir], check=False)

    if cmd_user:
        run_cmd(cmd_user, cwd=target_dir)
    if cmd_root:
        run_cmd(cmd_root, cwd=target_dir, as_root=True)

    log_success(f"Installation completed for {name}.")


def ensure_crudini():
    """Ensure crudini is installed."""
    if shutil.which("crudini") is None:
        log_warn("crudini not found, installing...")
        run_cmd("apt-get update && apt-get install -y crudini", as_root=True)


def ensure_slick_greeter_conf():
    """Ensure slick-greeter.conf exists."""
    greeter_conf = "/etc/lightdm/slick-greeter.conf"
    if not os.path.exists(greeter_conf):
        sample_conf = os.path.join(CONFIG_DIR, "slick-greeter.conf")
        if os.path.exists(sample_conf):
            log_info("Copying slick-greeter.conf template...")
            run_cmd(f"cp '{sample_conf}' '{greeter_conf}'", as_root=True)
        else:
            log_warn("No slick-greeter.conf template found in configs/.")
    else:
        log_info("slick-greeter.conf found.")


def apply_slick_greeter_theme(gtk_theme, icon_theme, cursor_theme):
    """Update /etc/lightdm/slick-greeter.conf using crudini."""
    ensure_crudini()
    ensure_slick_greeter_conf()

    greeter_conf = "/etc/lightdm/slick-greeter.conf"
    if not os.path.exists(greeter_conf):
        log_warn(f"{greeter_conf} still not found, skipping greeter config.")
        return

    run_cmd(f"crudini --set {greeter_conf} Greeter theme-name '{gtk_theme}'", as_root=True)
    run_cmd(f"crudini --set {greeter_conf} Greeter icon-theme-name '{icon_theme}'", as_root=True)
    run_cmd(f"crudini --set {greeter_conf} Greeter cursor-theme-name '{cursor_theme}'", as_root=True)
    log_success("Slick Greeter configuration updated successfully.")


# ---------------------------------------------------------------------
# dconf configuration method
# ---------------------------------------------------------------------
def apply_theme_dconf(gtk_theme, icon_theme, cursor_theme):
    """Apply selected themes by merging into existing dconf_base and loading it."""
    base_file = os.path.join(CONFIG_DIR, "dconf_base")
    if not os.path.exists(base_file):
        log_warn(f"{base_file} not found, creating minimal base...")
        base_content = "[org/cinnamon/desktop/interface]\n"
    else:
        with open(base_file, "r", encoding="utf-8") as f:
            base_content = f.read()

    lines = base_content.splitlines()
    new_lines = []
    in_iface = False
    in_wm = False

    for line in lines:
        stripped = line.strip()
        # Detect sections
        if stripped == "[org/cinnamon/desktop/interface]":
            in_iface = True
            in_wm = False
            new_lines.append(stripped)
            continue
        elif stripped == "[org/cinnamon/desktop/wm/preferences]":
            in_iface = False
            in_wm = True
            new_lines.append(stripped)
            continue
        elif stripped.startswith("[") and stripped.endswith("]"):
            in_iface = False
            in_wm = False
            new_lines.append(stripped)
            continue

        # Replace values in interface
        if in_iface:
            if stripped.startswith("gtk-theme="):
                new_lines.append(f"gtk-theme='{gtk_theme}'")
                continue
            elif stripped.startswith("icon-theme="):
                new_lines.append(f"icon-theme='{icon_theme}'")
                continue
            elif stripped.startswith("cursor-theme="):
                new_lines.append(f"cursor-theme='{cursor_theme}'")
                continue

        # Replace value in wm preferences
        if in_wm and stripped.startswith("theme="):
            new_lines.append(f"theme='{gtk_theme}'")
            continue

        # Preserve other lines
        new_lines.append(line)

    # Ensure missing keys are added
    if "[org/cinnamon/desktop/interface]" not in base_content:
        new_lines.insert(0, "[org/cinnamon/desktop/interface]")
        new_lines.insert(1, f"gtk-theme='{gtk_theme}'")
        new_lines.insert(2, f"icon-theme='{icon_theme}'")
        new_lines.insert(3, f"cursor-theme='{cursor_theme}'")

    if "[org/cinnamon/desktop/wm/preferences]" not in base_content:
        new_lines.append("[org/cinnamon/desktop/wm/preferences]")
        new_lines.append(f"theme='{gtk_theme}'")

    dconf_file = "/tmp/minty_theme.dconf"
    with open(dconf_file, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")

    log_info(f"Applying merged dconf snapshot ({dconf_file})...")
    run_cmd(f"sudo -u {USER_NAME} dconf load / < {dconf_file}")
    log_success("Theme applied successfully via merged dconf snapshot.")


# ---------------------------------------------------------------------
# Curses UI
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
        stdscr.addstr(1, max(0, w // 2 - len(title) // 2), title)
        stdscr.attroff(curses.color_pair(2))

        for idx, theme in enumerate(themes):
            line = f"{theme['name']} — {theme['description']}"
            x = max(2, w // 2 - len(line) // 2)
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
        elif key in [10, 13]:  # ENTER
            return themes[selected_idx]


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def run_curses_installer(stdscr):
    stdscr.clear()
    stdscr.addstr(2, 2, "[MintyForge] Preparing desktop environment...")
    stdscr.refresh()

    gtk = select_theme(stdscr, themes_data, "GTK")
    icon = select_theme(stdscr, icons_data, "Icon")
    cursor = select_theme(stdscr, cursors_data, "Cursor")

    stdscr.clear()
    stdscr.addstr(2, 2, "Installing selected themes...")
    stdscr.refresh()

    install_theme(gtk, f"{THEMES_DIR}/{gtk['name_to_use']}")
    install_theme(icon, f"{ICONS_DIR}/{icon['name_to_use']}")
    install_theme(cursor, f"{CURSORS_DIR}/{cursor['name_to_use']}")

    apply_theme_dconf(gtk["name_to_use"], icon["name_to_use"], cursor["name_to_use"])
    apply_slick_greeter_theme(gtk["name_to_use"], icon["name_to_use"], cursor["name_to_use"])

    stdscr.addstr(10, 2, "🎉 Theme installation and configuration completed successfully!")
    stdscr.addstr(12, 2, "Press any key to exit...")
    stdscr.refresh()
    stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(run_curses_installer)
