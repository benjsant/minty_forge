#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Distroscript Installer (fixed cwd)
-----------------------------------------------
Clones and runs the Distroscript repository safely from Python.
Ensures Podman and Distrobox are installed before running Distroscript.
Handles existing folders and executes the installation script from the repo root.

Security: Uses secure subprocess calls without shell=True
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for utils import
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    check_command_exists, apt_update, apt_install,
    run_command, git_clone, run_bash_script,
    info, success, warn, error
)

# -------- Helper Functions --------
# (None needed - using utils)

# -------- Podman installation --------
def ensure_podman():
    if not check_command_exists("podman"):
        info("Podman not found. Installing Podman...")
        apt_update()
        result = apt_install(["podman"])
        if not result.success:
            error("Failed to install Podman. Please install manually.")
            return False
        success("Podman installed successfully.")
    else:
        info("Podman is already installed.")
    return True

# -------- Distrobox installation --------
def ensure_distrobox():
    if not check_command_exists("distrobox"):
        info("Distrobox not found. Installing Distrobox...")
        # Install via curl | sh (complex command, use bash -c)
        result = run_command([
            "bash", "-c",
            "curl -s https://raw.githubusercontent.com/89luca89/distrobox/main/install | sudo sh"
        ])
        if not result.success:
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
        result = git_clone(repo_url, repo_dir)
        if result.success:
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
    result = run_bash_script(Path("./install.sh"), cwd=repo_dir)
    if result.success:
        success("Distroscript executed successfully.")
    else:
        error("Distroscript execution failed.")

# -------- Entrypoint --------
if __name__ == "__main__":
    install_distroscript()
