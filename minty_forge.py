#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MintyForge - Lanceur principal."""

import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path


URL = "http://localhost:5000"

_RED    = "\033[1;31m"
_GREEN  = "\033[1;32m"
_YELLOW = "\033[1;33m"
_RESET  = "\033[0m"


def _ok(msg):   print(f"{_GREEN}[OK]{_RESET}    {msg}")
def _warn(msg): print(f"{_YELLOW}[WARN]{_RESET}  {msg}")
def _fail(msg): print(f"{_RED}[ERREUR]{_RESET} {msg}")


def check_env():
    """Verifie l'environnement avant le lancement. Retourne False si bloquant."""
    ok = True

    # Python >= 3.10
    if sys.version_info < (3, 10):
        _fail(f"Python 3.10+ requis (version actuelle : {sys.version.split()[0]})")
        ok = False
    else:
        _ok(f"Python {sys.version.split()[0]}")

    # Flask
    try:
        import flask  # noqa: F401
        _ok("Flask disponible")
    except ImportError:
        _fail("Flask non installe. Lancez : pip install flask")
        ok = False

    # Pydantic
    try:
        import pydantic  # noqa: F401
        _ok("Pydantic disponible")
    except ImportError:
        _fail("Pydantic non installe. Lancez : pip install pydantic")
        ok = False

    # Outils systeme (non bloquants, simples avertissements)
    tools = {
        "dconf":     "requis pour l'application des themes (dump/load dconf)",
        "gsettings": "requis pour l'application des themes (greeter, etc.)",
        "apt":       "requis pour l'installation de paquets",
        "flatpak":   "optionnel — pour l'installation de Flatpaks",
        "git":       "optionnel — pour l'installation de themes depuis GitHub",
    }
    for tool, desc in tools.items():
        found = subprocess.run(["which", tool], capture_output=True).returncode == 0
        if found:
            _ok(tool)
        else:
            _warn(f"{tool} non trouve ({desc})")

    # Dossier configs
    if not (Path(__file__).parent / "configs").is_dir():
        _warn("Dossier configs/ absent — certaines fonctions seront vides")
    else:
        _ok("configs/ present")

    return ok


def open_browser():
    time.sleep(2)
    webbrowser.open(URL)


def main():
    web_app_path = Path(__file__).parent / "web_app.py"
    if not web_app_path.exists():
        _fail(f"web_app.py introuvable : {web_app_path}")
        return 1

    print()
    print("=" * 55)
    print("  MintyForge — Verification de l'environnement")
    print("=" * 55)
    if not check_env():
        print()
        _fail("Des dependances manquent. Corrigez les erreurs ci-dessus.")
        return 1

    print()
    print("=" * 55)
    print("  MintyForge — Lancement")
    print("=" * 55)
    print(f"  URL   : {URL}")
    print("  Arret : CTRL+C")
    print("=" * 55)
    print()

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        subprocess.run([sys.executable, str(web_app_path)])
    except KeyboardInterrupt:
        print("\n[OK] MintyForge arrete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
