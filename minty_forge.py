#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge – Main Script (Web Edition)
---------------------------------------
Launches the Flask web interface for MintyForge.
Modern web-based alternative to the curses menu.
Access via browser at http://localhost:5000

Compatible with Python 3.12+ (Linux Mint 22)
"""

import os
import sys
import subprocess
from pathlib import Path

# Note: Toutes les fonctionnalités sont maintenant dans web_app.py
# Ce fichier sert uniquement de lanceur pour l'interface web


# ---------------------------------------------------------------------
# Main Entrypoint
# ---------------------------------------------------------------------
def main():
    """MintyForge main entrypoint - launches web interface."""
    
    # Check if Flask is installed
    try:
        import flask
    except ImportError:
        print("\033[1;31m[ERROR]\033[0m Flask n'est pas installé.")
        print("Installation de Flask...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask"], check=False)
        print("\033[1;32m[OK]\033[0m Flask installé avec succès.")
    
    # Check web_app.py exists
    web_app_path = Path(__file__).parent / "web_app.py"
    if not web_app_path.exists():
        print("\033[1;31m[ERROR]\033[0m web_app.py introuvable!")
        print(f"Recherché dans : {web_app_path}")
        return
    
    print("\033[1;34m" + "="*60 + "\033[0m")
    print("\033[1;32m🛠️  MintyForge - Interface Web\033[0m")
    print("\033[1;34m" + "="*60 + "\033[0m")
    print("")
    print("Démarrage du serveur web...")
    print("")
    print("\033[1;33m📡 URL d'accès:\033[0m")
    print("   Local:   http://localhost:5000")
    print("   Réseau:  http://<votre-ip>:5000")
    print("")
    print("\033[1;36m💡 Astuce:\033[0m")
    print("   - Ouvrez l'URL dans votre navigateur")
    print("   - Utilisable depuis un autre PC du réseau")
    print("   - Appuyez sur CTRL+C pour arrêter")
    print("")
    print("\033[1;34m" + "="*60 + "\033[0m")
    print("")
    
    # Launch web_app.py
    try:
        subprocess.run([sys.executable, str(web_app_path)])
    except KeyboardInterrupt:
        print("\n")
        print("\033[1;32m[OK]\033[0m Arrêt de MintyForge. Au revoir!")
    except Exception as e:
        print(f"\033[1;31m[ERROR]\033[0m Erreur: {e}")


if __name__ == "__main__":
    main()
