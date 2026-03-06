#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Theme Installer
----------------------------------------------
Desktop theming utility for Linux Mint Cinnamon.
Installs GTK, Icon, and Cursor themes and applies them via dconf.
Updates Slick Greeter configuration if present.
Called by the Flask web interface.

Security Note: Theme cmd_user/cmd_root fields from JSON are executed via bash.
Ensure theme config files are trusted and not editable by untrusted users.
"""

import os
import json
import shutil
import shlex
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    info, success, warn, error,
    run_command, run_sudo_command, git_clone,
)

# ---------------------------------------------------------------------
# Project-root-relative paths (safe regardless of CWD)
# ---------------------------------------------------------------------
PROJECT_DIR = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_DIR / "configs"
THEMES_DIR = PROJECT_DIR / "themes"
ICONS_DIR = PROJECT_DIR / "icons"
CURSORS_DIR = PROJECT_DIR / "cursors"

for d in [THEMES_DIR, ICONS_DIR, CURSORS_DIR]:
    d.mkdir(exist_ok=True)

# ---------------------------------------------------------------------
# User detection
# ---------------------------------------------------------------------
USER_NAME = os.getenv("SUDO_USER") or os.getenv("USER")
USER_HOME = str(Path(f"~{USER_NAME}").expanduser()) if USER_NAME else ""

if not USER_NAME:
    error("Unable to detect user.")

# ---------------------------------------------------------------------
# Load JSON files
# ---------------------------------------------------------------------
def load_theme_json(file_path: Path):
    """Load themes from a JSON config file. Returns empty list on error."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)["themes"]
    except Exception as e:
        error(f"Failed to load {file_path}: {e}")
        return []

# ---------------------------------------------------------------------
# Installation helpers
# ---------------------------------------------------------------------
def install_theme(theme: dict, target_dir: Path):
    """Clone and install a theme sequentially."""
    name = theme.get("name", "unknown")
    url = theme.get("url", "")
    cmd_user = theme.get("cmd_user", "")
    cmd_root = theme.get("cmd_root", "")

    info(f"Installing {name}...")

    if url:
        if not target_dir.exists():
            info(f"Cloning {url} into {target_dir}")
            git_clone(url, target_dir, depth=1)
        else:
            warn(f"{target_dir} already exists. Skipping clone.")

    run_sudo_command(["chown", "-R", f"{USER_NAME}:{USER_NAME}", str(target_dir)])

    # cmd_user/cmd_root are shell commands from trusted JSON config
    if cmd_user:
        run_command(["bash", "-c", cmd_user], cwd=target_dir)
    if cmd_root:
        run_sudo_command(["bash", "-c", cmd_root], cwd=target_dir)

    success(f"{name} installed.")

def ensure_crudini():
    """Ensure crudini is installed for Slick Greeter config."""
    if shutil.which("crudini") is None:
        warn("crudini not found, installing...")
        run_sudo_command(["apt-get", "update"])
        run_sudo_command(["apt-get", "install", "-y", "crudini"])

def ensure_slick_greeter_conf():
    """Ensure slick-greeter.conf exists."""
    greeter_conf = Path("/etc/lightdm/slick-greeter.conf")
    if not greeter_conf.exists():
        sample_conf = CONFIG_DIR / "slick-greeter.conf"
        if sample_conf.exists():
            info("Copying slick-greeter.conf template...")
            run_sudo_command(["cp", str(sample_conf), str(greeter_conf)])
        else:
            warn("No slick-greeter.conf template found.")
    else:
        info("slick-greeter.conf found.")

def apply_slick_greeter_theme(gtk_theme, icon_theme, cursor_theme):
    """Update /etc/lightdm/slick-greeter.conf using crudini."""
    ensure_crudini()
    ensure_slick_greeter_conf()
    greeter_conf = "/etc/lightdm/slick-greeter.conf"

    run_sudo_command(["crudini", "--set", greeter_conf, "Greeter", "theme-name", gtk_theme])
    run_sudo_command(["crudini", "--set", greeter_conf, "Greeter", "icon-theme-name", icon_theme])
    run_sudo_command(["crudini", "--set", greeter_conf, "Greeter", "cursor-theme-name", cursor_theme])
    success("Slick Greeter updated.")

# ---------------------------------------------------------------------
# Theme application (dconf + gsettings)
# ---------------------------------------------------------------------
def apply_theme_gsettings(gtk_theme, icon_theme, cursor_theme):
    """Apply theme values using gsettings (applies immediately in session)."""
    settings = [
        ["gsettings", "set", "org.cinnamon.desktop.interface", "gtk-theme", gtk_theme],
        ["gsettings", "set", "org.cinnamon.desktop.interface", "icon-theme", icon_theme],
        ["gsettings", "set", "org.cinnamon.desktop.interface", "cursor-theme", cursor_theme],
        ["gsettings", "set", "org.cinnamon.desktop.wm.preferences", "theme", gtk_theme],
        ["gsettings", "set", "org.cinnamon.theme", "name", gtk_theme],
    ]
    any_ok = False
    for cmd in settings:
        result = run_command(cmd)
        if result.success:
            any_ok = True
        else:
            warn(f"gsettings failed: {' '.join(cmd)}")
    if any_ok:
        success("Theme applied via gsettings.")

def apply_theme_dconf(gtk_theme, icon_theme, cursor_theme):
    """Create dconf dump file and load it into current user session (no sudo)."""
    base_file = CONFIG_DIR / "dconf_base"
    if not base_file.exists():
        warn(f"{base_file} not found, creating minimal base...")
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
    info(f"Wrote dconf dump to {dconf_file}")

    # dconf load requires shell redirection
    result = run_command(["bash", "-c", f"dconf load / < {shlex.quote(dconf_file)}"])
    if not result.success:
        warn("dconf load failed. Applying via gsettings instead.")
        apply_theme_gsettings(gtk_theme, icon_theme, cursor_theme)
    else:
        success("Theme applied via dconf (including Cinnamon shell).")
        apply_theme_gsettings(gtk_theme, icon_theme, cursor_theme)

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def run_all_themes():
    """Install all themes and apply the first of each category."""
    themes_data = load_theme_json(CONFIG_DIR / "themes_gtk.json")
    icons_data = load_theme_json(CONFIG_DIR / "themes_icons.json")
    cursors_data = load_theme_json(CONFIG_DIR / "themes_cursors.json")

    if not themes_data or not icons_data or not cursors_data:
        error("Missing theme configuration files, aborting.")
        return

    info("Installing all GTK themes...")
    for theme in themes_data:
        install_theme(theme, THEMES_DIR / theme['name_to_use'])

    info("Installing all icon themes...")
    for theme in icons_data:
        install_theme(theme, ICONS_DIR / theme['name_to_use'])

    info("Installing all cursor themes...")
    for theme in cursors_data:
        install_theme(theme, CURSORS_DIR / theme['name_to_use'])

    # Apply the first theme of each category
    gtk_name = themes_data[0]['name_to_use']
    icon_name = icons_data[0]['name_to_use']
    cursor_name = cursors_data[0]['name_to_use']

    info(f"Applying themes: GTK={gtk_name}, Icons={icon_name}, Cursor={cursor_name}")
    apply_theme_dconf(gtk_name, icon_name, cursor_name)
    apply_slick_greeter_theme(gtk_name, icon_name, cursor_name)
    success("All themes installed and applied.")


def main():
    run_all_themes()


if __name__ == "__main__":
    main()
