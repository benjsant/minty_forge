#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Distroscript Installer (fixed cwd)
-----------------------------------------------
Clones and runs the Distroscript repository safely from Python.
Ensures Podman and Distrobox are installed before running Distroscript.
Handles existing folders and executes the installation script from the repo root.
"""

import os
import subprocess
from pathlib import Path

# -------- Terminal Colors --------
GREEN = "\033[1;32m"
BLUE = "\033[1;34m"
RED = "\033[1;31m"
YELLOW = "\033[1;33m"
RESET = "\033[0m"

# -------- Helper Functions --------
def info(msg: str):
    print(f"{BLUE}[INFO]{RESET} {msg}")

def success(msg: str):
    print(f"{GREEN}[OK]{RESET} {msg}")

def warn(msg: str):
    print(f"{YELLOW}[WARN]{RESET} {msg}")

def error(msg: str):
    print(f"{RED}[ERROR]{RESET} {msg}")

def run_cmd(cmd: str, cwd: Path | None = None) -> bool:
    """Run a shell command, optionally from a given working directory."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, cwd=str(cwd) if cwd else None)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        error(f"Command failed: {cmd}\n{e}")
        return False

# -------- Podman installation --------
def ensure_podman():
    if subprocess.run("command -v podman", shell=True, capture_output=True).returncode != 0:
        info("Podman not found. Installing Podman...")
        for cmd in ["sudo apt update", "sudo apt install -y podman"]:
            if not run_cmd(cmd):
                error("Failed to install Podman. Please install manually.")
                return False
        success("Podman installed successfully.")
    else:
        info("Podman is already installed.")
    return True

# -------- Distrobox installation --------
def ensure_distrobox():
    if subprocess.run("command -v distrobox", shell=True, capture_output=True).returncode != 0:
        info("Distrobox not found. Installing Distrobox...")
        cmd = "curl -s https://raw.githubusercontent.com/89luca89/distrobox/main/install | sudo sh"
        if not run_cmd(cmd):
            error("Failed to install Distrobox. Please install manually.")
            return False
        success("Distrobox installed successfully.")
    else:
        info("Distrobox is already installed.")
    return True

# -------- Main Logic --------
def install_distroscript():
    if not ensure_podman():
        error("Cannot proceed without Podman.")
        return

    if not ensure_distrobox():
        error("Cannot proceed without Distrobox.")
        return

    repo_dir = Path("distroscript").resolve()
    repo_url = "https://github.com/benjsant/distroscript.git"

    if not repo_dir.exists():
        info("Cloning Distroscript repository...")
        if run_cmd(f"git clone {repo_url} {repo_dir.parent / repo_dir.name}"):
            success("Repository cloned.")
        else:
            error("Failed to clone repository.")
            return
    else:
        info("Distroscript already exists, skipping clone.")

    install_sh = repo_dir / "install.sh"
    if not install_sh.exists():
        error("install.sh not found in Distroscript repository.")
        return

    if not os.access(install_sh, os.X_OK):
        info("Making install.sh executable...")
        os.chmod(install_sh, 0o755)

    info("Running Distroscript installer from its repository...")
    if run_cmd("./install.sh", cwd=repo_dir):
        success("Distroscript executed successfully.")
    else:
        error("Distroscript execution failed.")

# -------- Entrypoint --------
if __name__ == "__main__":
    install_distroscript()
