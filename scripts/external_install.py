#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - External Packages Installer
------------------------------------------
Installs external packages defined in configs/external_packages.json.
Called by the Flask web interface.

Security Note: External package commands from JSON are executed via bash.
Ensure external_packages.json is trusted and not editable by untrusted users.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    run_command,
    info, success, warn, error,
    get_state_manager, ACTION_EXTERNAL_INSTALL
)

CONFIG_FILE = Path(__file__).parent.parent / "configs/external_packages.json"


def install_package(pkg: dict):
    """Run the installation command for an external package."""
    name = pkg.get("name")
    desc = pkg.get("description", "")
    cmd = pkg.get("cmd")

    if not cmd:
        warn(f"No command defined for {name}, skipping.")
        return

    info(f"Installing {name} - {desc}...")
    result = run_command(["bash", "-c", cmd])

    get_state_manager().record(
        action=ACTION_EXTERNAL_INSTALL,
        target=name,
        success=result.success,
        rollback_cmd=[],
        metadata={"description": desc, "manual_rollback": True},
    )

    if result.success:
        success(f"{name} installed successfully.")
    else:
        warn(f"Failed to install {name}.")


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

    packages = data.get("external_packages", data.get("packages", []))
    if not packages:
        warn("No external packages found.")
        return

    info("Installing all external packages...")
    for pkg in packages:
        install_package(pkg)
    success("All external packages processed.")


if __name__ == "__main__":
    main()
