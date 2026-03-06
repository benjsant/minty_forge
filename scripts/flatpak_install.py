#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Flatpak Installer
---------------------------------
Installs all Flatpak apps defined in configs/flatpak.json.
Called by the Flask web interface.

Security: Uses secure subprocess calls without shell=True
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    check_flatpak_installed, flatpak_install,
    info, success, warn, error,
    get_state_manager, ACTION_FLATPAK_INSTALL
)

CONFIG_FILE = Path(__file__).parent.parent / "configs/flatpak.json"


def install_single_flatpak(flatpak: dict):
    """Install a single Flatpak app."""
    app = flatpak.get("app")
    source = flatpak.get("source", "flathub")
    desc = flatpak.get("description", "")

    if not app:
        warn("Empty Flatpak ID, skipping.")
        return

    if check_flatpak_installed(app):
        warn(f"{app} is already installed, skipping.")
        return

    info(f"Installing {app} - {desc} from {source}...")
    result = flatpak_install(app, remote=source)

    get_state_manager().record(
        action=ACTION_FLATPAK_INSTALL,
        target=app,
        success=result.success,
        rollback_cmd=["flatpak", "uninstall", "-y", app],
        metadata={"description": desc, "source": source},
    )

    if result.success:
        success(f"{app} installed successfully.")
    else:
        warn(f"Failed to install {app}.")


def install_all_flatpaks(flatpaks: list[dict]):
    """Install all Flatpaks from the list."""
    info("Starting installation of all Flatpaks...")
    for flatpak in flatpaks:
        install_single_flatpak(flatpak)
    success("All Flatpaks processed.")


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

    flatpaks = data.get("flatpaks", [])
    if not flatpaks:
        warn("No Flatpaks found in config.")
        return

    install_all_flatpaks(flatpaks)


if __name__ == "__main__":
    main()
