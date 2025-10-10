#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Distroscript Installer
-----------------------------------
Clones and runs the Distroscript repository safely from Python.
Handles existing folders and executes the installation script.
"""

import os
import subprocess
from pathlib import Path

# -------- Terminal Colors --------
GREEN = "\033[1;32m"
BLUE = "\033[1;34m"
RED = "\033[1;31m"
RESET = "\033[0m"

# -------- Helper Functions --------
def info(msg: str):
    print(f"{BLUE}[INFO]{RESET} {msg}")

def success(msg: str):
    print(f"{GREEN}[OK]{RESET} {msg}")

def error(msg: str):
    print(f"{RED}[ERROR]{RESET} {msg}")

def run_cmd(cmd: str) -> bool:
    """Run a shell command, returning True if successful."""
    try:
        result = subprocess.run(cmd, shell=True, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        error(f"Command failed: {cmd}\n{e}")
        return False

# -------- Main Logic --------
def install_distroscript():
    repo_dir = Path("distroscript")
    repo_url = "https://github.com/benjsant/distroscript.git"

    if not repo_dir.exists():
        info("Cloning Distroscript repository...")
        if run_cmd(f"git clone {repo_url} {repo_dir}"):
            success("Repository cloned.")
        else:
            error("Failed to clone repository.")
            return
    else:
        info("Distroscript already exists, skipping clone.")

    os.chdir(repo_dir)
    info("Running Distroscript installer...")

    # Vérifie que le fichier install.sh existe et est exécutable
    if not Path("install.sh").exists():
        error("install.sh not found in Distroscript repository.")
        return

    if not os.access("install.sh", os.X_OK):
        info("Making install.sh executable...")
        os.chmod("install.sh", 0o755)

    # Exécution du script
    if run_cmd("./install.sh"):
        success("Distroscript executed successfully.")
    else:
        error("Distroscript execution failed.")

# -------- Entrypoint --------
if __name__ == "__main__":
    install_distroscript()
