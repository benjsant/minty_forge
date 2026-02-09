#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Script de lancement simple
----------------------------------------
Lance l'interface web MintyForge.
Compatible Python 3.12+ (pyenv ou système)
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Lance MintyForge avec validation de l'environnement."""
    
    # Vérifier Flask
    try:
        import flask
        print(f"✅ Flask {flask.__version__} détecté")
    except ImportError:
        print("❌ Flask non installé!")
        print("\n🔧 Installation de Flask...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask"], check=True)
        print("✅ Flask installé avec succès\n")
    
    # Vérifier Pydantic
    try:
        import pydantic
        print(f"✅ Pydantic {pydantic.__version__} détecté")
    except ImportError:
        print("❌ Pydantic non installé!")
        print("\n🔧 Installation de Pydantic...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pydantic"], check=True)
        print("✅ Pydantic installé avec succès\n")
    
    # Lancer l'application
    print("\n" + "="*60)
    print("🛠️  MintyForge v2.2.0 - Interface Web")
    print("="*60)
    print("\n📡 Serveur disponible sur:")
    print("   → http://localhost:5000")
    print("\n💡 Appuyez sur CTRL+C pour arrêter\n")
    print("="*60 + "\n")
    
    # Importer et lancer Flask
    web_app_path = Path(__file__).parent / "web_app.py"
    
    try:
        # Lance comme module
        subprocess.run([sys.executable, str(web_app_path)])
    except KeyboardInterrupt:
        print("\n\n✅ Arrêt de MintyForge. Au revoir!")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
