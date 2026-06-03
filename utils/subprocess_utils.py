#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wrappers subprocess securises (pas de shell=True)."""

import sys
import subprocess
from pathlib import Path


# Timeout par defaut pour toute commande sans valeur explicite.
# Empeche qu'un processus qui pendouille (reseau coupe, prompt cache, etc.)
# bloque indefiniment la file de taches du serveur.
DEFAULT_COMMAND_TIMEOUT = 600  # 10 min
GIT_CLONE_TIMEOUT = 300        # 5 min


class CommandResult:
    """Resultat d'une commande."""
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.success = returncode == 0

    def __bool__(self):
        return self.success


def run_command(cmd, check=False, capture_output=False, cwd=None, timeout=None, env=None):
    """Execute une commande (liste d'args, pas de shell).

    Si `timeout` est None, applique DEFAULT_COMMAND_TIMEOUT (10 min) pour eviter
    qu'un processus qui pendouille bloque la file de taches du serveur.
    Passer explicitement timeout=0 pour desactiver (par exemple commandes
    interactives ou daemons).
    """
    effective_timeout = DEFAULT_COMMAND_TIMEOUT if timeout is None else (timeout or None)
    try:
        result = subprocess.run(
            cmd, check=check, capture_output=capture_output, text=True,
            cwd=str(cwd) if cwd else None, timeout=effective_timeout, env=env
        )
        return CommandResult(
            result.returncode,
            result.stdout if capture_output else "",
            result.stderr if capture_output else ""
        )
    except subprocess.CalledProcessError as e:
        return CommandResult(e.returncode, e.stdout or "", e.stderr or "")
    except subprocess.TimeoutExpired:
        return CommandResult(-1, "", "Timeout")
    except FileNotFoundError as e:
        return CommandResult(-1, "", f"Commande introuvable : {e}")


def run_sudo_command(cmd, check=False, capture_output=False, timeout=None):
    """Execute avec sudo -n (echoue si mot de passe requis)."""
    return run_command(["sudo", "-n"] + cmd, check=check,
                       capture_output=capture_output, timeout=timeout)


def check_package_installed(package_name):
    """Verifie si un paquet deb est installe (via dpkg-query)."""
    result = run_command(
        ["dpkg-query", "-W", "-f=${Status}", package_name],
        capture_output=True
    )
    return "install ok installed" in result.stdout


def check_command_exists(command):
    """Verifie si une commande existe dans le PATH."""
    return run_command(["which", command], capture_output=True).success


def _accept_msfonts_eula():
    """Pre-accepte la licence Microsoft pour ttf-mscorefonts-installer (evite le prompt interactif)."""
    run_command(
        ["sudo", "-n", "bash", "-c",
         "echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections"],
    )


# Paquets qui declenchent le prompt EULA des polices Microsoft
_MSFONTS_TRIGGERS = {"ubuntu-restricted-extras", "ttf-mscorefonts-installer", "kubuntu-restricted-extras", "xubuntu-restricted-extras"}


# Timeouts (en secondes) pour eviter qu'un dépôt distant qui pendouille
# bloque toute la file de taches.
APT_INSTALL_TIMEOUT = 1800   # 30 min : gros paquets + dependances
APT_REMOVE_TIMEOUT = 600     # 10 min
APT_UPDATE_TIMEOUT = 300     # 5 min
APT_UPGRADE_TIMEOUT = 3600   # 1 h : upgrade complet
FLATPAK_INSTALL_TIMEOUT = 1800


def apt_install(packages, assume_yes=True):
    if _MSFONTS_TRIGGERS.intersection(packages):
        _accept_msfonts_eula()
    cmd = ["apt", "install"]
    if assume_yes:
        cmd.append("-y")
    cmd.extend(packages)
    return run_sudo_command(cmd, timeout=APT_INSTALL_TIMEOUT)


def apt_remove(packages, purge=False, assume_yes=True):
    cmd = ["apt", "purge" if purge else "remove"]
    if assume_yes:
        cmd.append("-y")
    cmd.extend(packages)
    return run_sudo_command(cmd, timeout=APT_REMOVE_TIMEOUT)


def apt_update():
    return run_sudo_command(["apt", "update"], timeout=APT_UPDATE_TIMEOUT)


def apt_upgrade(assume_yes=True):
    cmd = ["apt", "upgrade"]
    if assume_yes:
        cmd.append("-y")
    return run_sudo_command(cmd, timeout=APT_UPGRADE_TIMEOUT)


def flatpak_install(app_id, remote="flathub", assume_yes=True):
    cmd = ["flatpak", "install"]
    if assume_yes:
        cmd.append("-y")
    cmd.extend([remote, app_id])
    return run_command(cmd, timeout=FLATPAK_INSTALL_TIMEOUT)


def flatpak_list():
    """Liste les applis Flatpak installees."""
    result = run_command(["flatpak", "list", "--app", "--columns=application"],
                         capture_output=True)
    if result.success:
        return [line.strip() for line in result.stdout.split('\n') if line.strip()]
    return []


def check_flatpak_installed(app_id):
    """Verifie si un Flatpak est installe (via flatpak info)."""
    return run_command(["flatpak", "info", app_id], capture_output=True).success


def git_clone(repo_url, target_dir, depth=None):
    cmd = ["git", "clone"]
    if depth:
        cmd.extend(["--depth", str(depth)])
    cmd.extend([repo_url, str(target_dir)])
    return run_command(cmd, timeout=GIT_CLONE_TIMEOUT)


def run_bash_script(script_path, args=None, cwd=None):
    cmd = ["bash", str(script_path)]
    if args:
        cmd.extend(args)
    return run_command(cmd, cwd=cwd)


def run_python_script(script_path, args=None, cwd=None):
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    return run_command(cmd, cwd=cwd)
