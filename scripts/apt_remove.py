#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Supprime les paquets APT definis dans configs/remove.json."""

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


def remove_single_package(pkg):
    name = pkg.get("name")
    desc = pkg.get("description", "")
    if not name:
        warn("Nom de paquet vide, ignore.")
        return

    info(f"Verification de {name}...")
    if check_package_installed(name):
        info(f"Suppression de {name} ({desc})...")
        result = apt_remove([name], purge=True)

        get_state_manager().record(
            action=ACTION_APT_REMOVE,
            target=name,
            success=result.success,
            rollback_cmd=["apt", "install", "-y", name],
            metadata={"description": desc},
        )

        if result.success:
            success(f"{name} supprime.")
        else:
            warn(f"Echec suppression de {name}.")
    else:
        warn(f"{name} pas installe, ignore.")


def remove_all_packages(packages):
    info("Suppression des paquets indesirables...")
    for pkg in packages:
        remove_single_package(pkg)
    run_sudo_command(["apt", "autoremove", "-y"])
    success("Nettoyage termine.")


def main():
    if not CONFIG_FILE.exists():
        error(f"{CONFIG_FILE} introuvable.")
        return

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        error(f"JSON invalide dans {CONFIG_FILE}: {e}")
        return

    packages = data.get("packages", [])
    if not packages:
        warn("Aucun paquet dans la config.")
        return

    remove_all_packages(packages)


if __name__ == "__main__":
    main()
