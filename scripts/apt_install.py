#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - APT Installer
----------------------------
Installs all APT packages defined in configs/install.json.
Called by the Flask web interface.

Security: Uses secure subprocess calls without shell=True
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    check_package_installed, apt_install,
    info, success, warn, error,
    load_package_list,
    get_state_manager, ACTION_APT_INSTALL
)

CONFIG_FILE = Path(__file__).parent.parent / "configs/install.json"


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

    get_state_manager().record(
        action=ACTION_APT_INSTALL,
        target=name,
        success=result.success,
        rollback_cmd=["apt", "remove", "-y", name],
        metadata={"description": desc},
    )

    if result.success:
        success(f"{name} installed successfully.")
    else:
        warn(f"Failed to install {name}.")


def install_all_packages(packages: list[dict]):
    """Install all packages from the list."""
    info("Starting installation of all packages...")

    for pkg in packages:
        install_single_package(pkg)

    success("All packages processed.")


def main():
    if not CONFIG_FILE.exists():
        error(f"{CONFIG_FILE} not found.")
        return

    try:
        packages = load_package_list(CONFIG_FILE)
    except Exception as e:
        error(f"Failed to load config: {e}")
        return

    if not packages:
        warn("No packages found in config.")
        return

    install_all_packages(packages)


if __name__ == "__main__":
    main()
