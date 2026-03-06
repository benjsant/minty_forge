#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - APT Remover
--------------------------
Removes unwanted APT packages defined in configs/remove.json.
Called by the Flask web interface.

Security: Uses secure subprocess calls without shell=True
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    check_package_installed, apt_remove, run_sudo_command,
    info, success, warn, error,
    get_state_manager, ACTION_APT_REMOVE
)

CONFIG_FILE = Path(__file__).parent.parent / "configs/remove.json"


def remove_single_package(pkg: dict):
    """Remove a single package."""
    name = pkg.get("name")
    desc = pkg.get("description", "")
    if not name:
        warn("Empty package name, skipping.")
        return

    info(f"Checking {name}...")
    if check_package_installed(name):
        info(f"Removing {name} ({desc})...")
        result = apt_remove([name], purge=True)

        get_state_manager().record(
            action=ACTION_APT_REMOVE,
            target=name,
            success=result.success,
            rollback_cmd=["apt", "install", "-y", name],
            metadata={"description": desc},
        )

        if result.success:
            success(f"{name} removed successfully.")
        else:
            warn(f"Failed to remove {name}.")
    else:
        warn(f"{name} not installed, skipping.")


def remove_all_packages(packages: list[dict]):
    """Remove all packages from the config."""
    info("Removing all unwanted packages...")

    for pkg in packages:
        remove_single_package(pkg)

    run_sudo_command(["apt", "autoremove", "-y"])
    success("All unwanted packages removed.")


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
        warn("No packages found in config.")
        return

    remove_all_packages(packages)


if __name__ == "__main__":
    main()
