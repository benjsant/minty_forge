#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge – Theme Installer (Curses Edition)
----------------------------------------------
Interactive desktop theming utility for Linux Mint Cinnamon.
Installs GTK, Icon, and Cursor themes sequentially and applies them via dconf.
Updates Slick Greeter configuration if present.
"""

import os
import json
import curses
import subprocess
import shutil
import logging
import shlex
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

CONFIG_DIR = Path("./configs")
THEMES_DIR = Path("./themes")
ICONS_DIR = Path("./icons")
CURSORS_DIR = Path("./cursors")

for d in [THEMES_DIR, ICONS_DIR, CURSORS_DIR]:
    d.mkdir(exist_ok=True)

# ---------------------------------------------------------------------
# Load JSON files
# ---------------------------------------------------------------------
def load_json(file_path: Path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)["themes"]
    except Exception as e:
        log_error(f"Failed to load {file_path}: {e}")
        exit(1)

themes_data = load_json(CONFIG_DIR / "themes_gtk.json")
icons_data = load_json(CONFIG_DIR / "themes_icons.json")
cursors_data = load_json(CONFIG_DIR / "themes_cursors.json")

# ---------------------------------------------------------------------
# Helper: safe command runner
# ---------------------------------------------------------------------
def run_cmd(cmd: str, cwd=None, as_root=False, timeout=60):
    """
    Execute shell command, capture output, return (ok, stdout, stderr).
    - as_root: uses sudo if not already root.
    - does NOT block waiting for password.
    """
    if as_root:
        if os.geteuid() == 0:
            full_cmd = ["bash", "-c", cmd]
        else:
            full_cmd = ["sudo", "-n", "bash", "-c", cmd]
    else:
        full_cmd = ["bash", "-c", cmd]

    try:
        proc = subprocess.run(
            full_cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy(),
        )
        if proc.stdout.strip():
            log_info(proc.stdout.strip())
        if proc.stderr.strip():
            log_warn(proc.stderr.strip())
        return True, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        log_error(f"Command timed out: {cmd}")
        return False, "", "timeout"
    except subprocess.CalledProcessError as e:
        log_warn(f"Command failed: {cmd}\n{e.stderr}")
        return False, e.stdout, e.stderr
    except Exception as e:
        log_error(f"Unexpected error running command: {cmd}\n{e}")
        return False, "", str(e)

# ---------------------------------------------------------------------
# Installation helpers
# ---------------------------------------------------------------------
def install_theme(theme: dict, target_dir: Path):
    """Clone and install a theme sequentially (improved logging)."""
    name = theme.get("name", "unknown")
    url = theme.get("url", "")
    cmd_user = theme.get("cmd_user", "")
    cmd_root = theme.get("cmd_root", "")

    log_info(f"Installing {name}...")

    if url:
        if not target_dir.exists():
            log_info(f"Cloning {url} into {target_dir}")
            run_cmd(f"git clone --depth=1 {shlex.quote(url)} {shlex.quote(str(target_dir))}", timeout=120)
        else:
            log_warn(f"{target_dir} already exists. Skipping clone.")

    run_cmd(f"chown -R {shlex.quote(USER_NAME)}:{shlex.quote(USER_NAME)} {shlex.quote(str(target_dir))}", as_root=True)

    if cmd_user:
        run_cmd(cmd_user, cwd=str(target_dir))
    if cmd_root:
        run_cmd(cmd_root, cwd=str(target_dir), as_root=True)

    log_success(f"{name} installed.")

def ensure_crudini():
    """Ensure crudini is installed for Slick Greeter config."""
    if shutil.which("crudini") is None:
        log_warn("crudini not found, installing...")
        run_cmd("apt-get update && apt-get install -y crudini", as_root=True)

def ensure_slick_greeter_conf():
    """Ensure slick-greeter.conf exists."""
    greeter_conf = "/etc/lightdm/slick-greeter.conf"
    if not os.path.exists(greeter_conf):
        sample_conf = CONFIG_DIR / "slick-greeter.conf"
        if sample_conf.exists():
            log_info("Copying slick-greeter.conf template...")
            run_cmd(f"cp '{sample_conf}' '{greeter_conf}'", as_root=True)
        else:
            log_warn("No slick-greeter.conf template found.")
    else:
        log_info("slick-greeter.conf found.")

def apply_slick_greeter_theme(gtk_theme, icon_theme, cursor_theme):
    """Update /etc/lightdm/slick-greeter.conf using crudini."""
    ensure_crudini()
    ensure_slick_greeter_conf()
    greeter_conf = "/etc/lightdm/slick-greeter.conf"

    run_cmd(f"crudini --set {greeter_conf} Greeter theme-name '{gtk_theme}'", as_root=True)
    run_cmd(f"crudini --set {greeter_conf} Greeter icon-theme-name '{icon_theme}'", as_root=True)
    run_cmd(f"crudini --set {greeter_conf} Greeter cursor-theme-name '{cursor_theme}'", as_root=True)
    log_success("Slick Greeter updated.")

# ---------------------------------------------------------------------
# Theme application (dconf + gsettings)
# ---------------------------------------------------------------------
def apply_theme_gsettings(gtk_theme, icon_theme, cursor_theme):
    """Apply theme values using gsettings (applies immediately in session)."""
    cmds = [
        f"gsettings set org.cinnamon.desktop.interface gtk-theme '{gtk_theme}'",
        f"gsettings set org.cinnamon.desktop.interface icon-theme '{icon_theme}'",
        f"gsettings set org.cinnamon.desktop.interface cursor-theme '{cursor_theme}'",
        f"gsettings set org.cinnamon.desktop.wm.preferences theme '{gtk_theme}'",
        f"gsettings set org.cinnamon.theme name '{gtk_theme}'",
    ]
    any_ok = False
    for c in cmds:
        ok, _, err = run_cmd(c)
        if ok:
            any_ok = True
        else:
            log_warn(f"gsettings failed: {c} -> {err}")
    if any_ok:
        log_success("Theme applied via gsettings.")

def apply_theme_dconf(gtk_theme, icon_theme, cursor_theme):
    """Create dconf dump file and load it into current user session (no sudo)."""
    base_file = CONFIG_DIR / "dconf_base"
    if not base_file.exists():
        log_warn(f"{base_file} not found, creating minimal base...")
        base_content = "[org/cinnamon/desktop/interface]\n"
    else:
        base_content = base_file.read_text(encoding="utf-8")

    new_lines = []
    in_iface = False
    in_wm = False
    in_shell = False

    for line in base_content.splitlines():
        stripped = line.strip()

        if stripped == "[org/cinnamon/desktop/interface]":
            in_iface, in_wm, in_shell = True, False, False
            new_lines.append(stripped)
            continue
        elif stripped == "[org/cinnamon/desktop/wm/preferences]":
            in_iface, in_wm, in_shell = False, True, False
            new_lines.append(stripped)
            continue
        elif stripped == "[org/cinnamon/theme]":
            in_iface, in_wm, in_shell = False, False, True
            new_lines.append(stripped)
            continue
        elif stripped.startswith("[") and stripped.endswith("]"):
            in_iface = in_wm = in_shell = False
            new_lines.append(stripped)
            continue

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
        elif in_wm and stripped.startswith("theme="):
            new_lines.append(f"theme='{gtk_theme}'")
            continue
        elif in_shell and stripped.startswith("name="):
            new_lines.append(f"name='{gtk_theme}'")
            continue

        new_lines.append(line)

    # Ensure missing sections are appended
    if "[org/cinnamon/desktop/interface]" not in base_content:
        new_lines.append("[org/cinnamon/desktop/interface]")
        new_lines.append(f"gtk-theme='{gtk_theme}'")
        new_lines.append(f"icon-theme='{icon_theme}'")
        new_lines.append(f"cursor-theme='{cursor_theme}'")

    if "[org/cinnamon/desktop/wm/preferences]" not in base_content:
        new_lines.append("[org/cinnamon/desktop/wm/preferences]")
        new_lines.append(f"theme='{gtk_theme}'")

    if "[org/cinnamon/theme]" not in base_content:
        new_lines.append("[org/cinnamon/theme]")
        new_lines.append(f"name='{gtk_theme}'")

    # Write new dconf data
    dconf_file = "/tmp/minty_theme.dconf"
    Path(dconf_file).write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    log_info(f"Wrote dconf dump to {dconf_file}")

    ok, _, err = run_cmd(f"dconf load / < {shlex.quote(dconf_file)}")
    if not ok:
        log_warn(f"dconf load failed: {err}. Applying via gsettings instead.")
        apply_theme_gsettings(gtk_theme, icon_theme, cursor_theme)
    else:
        log_success("Theme applied via dconf (including Cinnamon shell).")
        apply_theme_gsettings(gtk_theme, icon_theme, cursor_theme)

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
            line = f"{theme['name']} — {theme.get('description','')}"
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
        elif key in [10, 13]:
            return themes[selected_idx]

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def run_curses_installer(stdscr):
    stdscr.clear()
    stdscr.addstr(2, 2, "[MintyForge] Preparing desktop environment...")
    stdscr.refresh()

    gtk_theme = select_theme(stdscr, themes_data, "GTK")
    icon_theme = select_theme(stdscr, icons_data, "Icon")
    cursor_theme = select_theme(stdscr, cursors_data, "Cursor")

    stdscr.clear()
    stdscr.addstr(2, 2, "Installing selected themes...")
    stdscr.refresh()

    install_theme(gtk_theme, THEMES_DIR / gtk_theme['name_to_use'])
    install_theme(icon_theme, ICONS_DIR / icon_theme['name_to_use'])
    install_theme(cursor_theme, CURSORS_DIR / cursor_theme['name_to_use'])

    apply_theme_dconf(gtk_theme['name_to_use'], icon_theme['name_to_use'], cursor_theme['name_to_use'])
    apply_slick_greeter_theme(gtk_theme['name_to_use'], icon_theme['name_to_use'], cursor_theme['name_to_use'])

    stdscr.addstr(10, 2, "🎉 Theme installation and configuration completed successfully!")
    stdscr.addstr(12, 2, "Press any key to exit...")
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(run_curses_installer)
