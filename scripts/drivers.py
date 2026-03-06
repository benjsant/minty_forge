#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Driver Installation
---------------------------------
Installs recommended drivers via CLI using 'ubuntu-drivers autoinstall'.
Called by the Flask web interface.
"""

import subprocess


def install_drivers_cli():
    """Install recommended drivers via CLI (no GUI needed)."""
    print("[MintyForge] Detecting and installing recommended drivers...")
    try:
        # List recommended drivers first
        result = subprocess.run(
            ["sudo", "-n", "ubuntu-drivers", "list"],
            capture_output=True, text=True, timeout=60
        )
        if result.stdout.strip():
            print(f"[INFO] Recommended drivers: {result.stdout.strip()}")
        else:
            print("[INFO] No additional drivers recommended.")
            return

        # Install them
        result = subprocess.run(
            ["sudo", "-n", "ubuntu-drivers", "autoinstall"],
            capture_output=False, text=True, timeout=600
        )
        if result.returncode == 0:
            print("[OK] Drivers installed successfully.")
        else:
            print("[WARN] Driver installation finished with warnings.")
    except FileNotFoundError:
        print("[WARN] ubuntu-drivers not found. Skipping driver installation.")
    except subprocess.TimeoutExpired:
        print("[ERROR] Driver installation timed out.")
    except subprocess.CalledProcessError:
        print("[WARN] Driver installation exited with an error.")


def main():
    install_drivers_cli()


if __name__ == "__main__":
    main()
