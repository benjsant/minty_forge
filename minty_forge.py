#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Main Launcher
---------------------------------------
Launches the Flask web interface and opens the browser automatically.
Usage: python3 minty_forge.py
"""

import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path


URL = "http://localhost:5000"


def open_browser():
    """Open the browser after a short delay to let Flask start."""
    time.sleep(2)
    webbrowser.open(URL)


def main():
    web_app_path = Path(__file__).parent / "web_app.py"
    if not web_app_path.exists():
        print(f"[ERROR] web_app.py introuvable: {web_app_path}")
        return 1

    print("=" * 60)
    print("MintyForge - Interface Web")
    print("=" * 60)
    print()
    print(f"URL: {URL}")
    print("Arret: CTRL+C")
    print()

    # Open browser in background thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    try:
        subprocess.run([sys.executable, str(web_app_path)])
    except KeyboardInterrupt:
        print("\n[OK] MintyForge arrete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
