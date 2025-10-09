#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Launch Mint Drivers
--------------------------------
Simple wrapper to run 'mintdrivers' from Python.
"""

import subprocess

def main():
    print("[MintyForge] Launching Mint Drivers...")
    try:
        subprocess.run(["sudo", "mintdrivers"], check=True)
        print("✅ Mint Drivers finished.")
    except subprocess.CalledProcessError:
        print("⚠️ Mint Drivers exited with an error.")

if __name__ == "__main__":
    main()
