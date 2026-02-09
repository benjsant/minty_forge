#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Script de lancement simple
----------------------------------------
Lance l'interface web Flask sur http://localhost:5000
"""

import sys
import subprocess
from pathlib import Path


def check_dependencies():
    """Vérifie que Flask et Pydantic sont installés."""
    missing = []
    
    try:
        import flask
        print(f"✅ Flask {flask.__version__}")
    except ImportError:
        missing.append("flask")
    
    try:
        import pydantic
        print(f"✅ Pydantic {pydantic.__version__}")
    except ImportError:
        missing.append("pydantic")
    
    if missing:
        print(f"\n❌ Dépendances manquantes : {', '.join(missing)}")
        print(f"\n📦 Installation...")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)
        print("✅ Dépendances installées\n")
    
    return True


def main():
    """Lance MintyForge."""
    print("="*60)
    print("🛠️  MintyForge - Lancement")
    print("="*60)
    print()
    
    # Vérifier dépendances
    check_dependencies()
    
    # Vérifier web_app.py
    web_app = Path(__file__).parent / "web_app.py"
    if not web_app.exists():
        print(f"❌ Erreur : {web_app} introuvable")
        return 1
    
    print("🚀 Démarrage du serveur Flask...")
    print()
    print("📡 Accès : http://localhost:5000")
    print("⏹️  Arrêt : CTRL+C")
    print()
    print("="*60)
    print()
    
    try:
        # Lancer web_app.py directement
        subprocess.run([sys.executable, str(web_app)])
    except KeyboardInterrupt:
        print("\n\n✅ Arrêt de MintyForge")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
