#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Setup et Lancement Automatique
--------------------------------------------
Script d'installation et de lancement tout-en-un :
1. Vérifie les dépendances système
2. Crée un environnement virtuel (venv)
3. Installe les dépendances Python
4. Lance l'application Flask
5. Ouvre le navigateur automatiquement

Usage: python3 setup_and_run.py
"""

import os
import sys
import subprocess
import platform
import webbrowser
import time
from pathlib import Path


class MintyForgeSetup:
    """Gestionnaire d'installation et de lancement."""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent.resolve()
        self.venv_dir = self.project_dir / ".venv"
        self.requirements_file = self.project_dir / "requirements.txt"
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    def print_header(self, text):
        """Affiche un en-tête formaté."""
        print("\n" + "="*70)
        print(f"🛠️  {text}")
        print("="*70)
    
    def print_step(self, number, text):
        """Affiche une étape numérotée."""
        print(f"\n📋 Étape {number} : {text}")
        print("-"*70)
    
    def print_success(self, text):
        """Affiche un message de succès."""
        print(f"✅ {text}")
    
    def print_info(self, text):
        """Affiche une information."""
        print(f"ℹ️  {text}")
    
    def print_warning(self, text):
        """Affiche un avertissement."""
        print(f"⚠️  {text}")
    
    def print_error(self, text):
        """Affiche une erreur."""
        print(f"❌ {text}")
    
    def check_python_version(self):
        """Vérifie que Python 3.8+ est utilisé."""
        self.print_step(1, "Vérification de Python")
        
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.print_error(f"Python 3.8+ requis (actuellement : {self.python_version})")
            return False
        
        self.print_success(f"Python {self.python_version} détecté")
        self.print_info(f"Exécutable : {sys.executable}")
        return True
    
    def check_system_dependencies(self):
        """Vérifie les dépendances système."""
        self.print_step(2, "Vérification des dépendances système")
        
        # Vérifier pip
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                check=True,
                capture_output=True
            )
            self.print_success("pip est installé")
        except subprocess.CalledProcessError:
            self.print_error("pip n'est pas installé")
            self.print_info("Installation de pip...")
            
            # Essayer d'installer pip
            try:
                subprocess.run(
                    [sys.executable, "-m", "ensurepip", "--default-pip"],
                    check=True
                )
                self.print_success("pip installé avec succès")
            except:
                self.print_error("Impossible d'installer pip automatiquement")
                self.print_info("Installez pip manuellement : sudo apt install python3-pip")
                return False
        
        # Vérifier venv
        try:
            import venv
            self.print_success("Module venv disponible")
        except ImportError:
            self.print_warning("Module venv non disponible")
            
            if platform.system() == "Linux":
                self.print_info("Sur Linux, installez : sudo apt install python3-venv")
                
                # Proposer installation automatique
                response = input("\n❓ Voulez-vous installer python3-venv maintenant ? (o/N) : ")
                if response.lower() in ('o', 'oui', 'y', 'yes'):
                    try:
                        subprocess.run(
                            ["sudo", "apt", "install", "-y", "python3-venv"],
                            check=True
                        )
                        self.print_success("python3-venv installé")
                    except:
                        self.print_error("Échec de l'installation")
                        return False
                else:
                    return False
            else:
                self.print_error("Le module venv est requis")
                return False
        
        return True
    
    def create_venv(self):
        """Crée l'environnement virtuel."""
        self.print_step(3, "Création de l'environnement virtuel")
        
        if self.venv_dir.exists():
            self.print_info(f"Environnement virtuel déjà présent : {self.venv_dir}")
            response = input("\n❓ Voulez-vous le recréer ? (o/N) : ")
            
            if response.lower() in ('o', 'oui', 'y', 'yes'):
                self.print_info("Suppression de l'ancien venv...")
                import shutil
                shutil.rmtree(self.venv_dir)
            else:
                self.print_info("Réutilisation du venv existant")
                return True
        
        try:
            self.print_info(f"Création de venv dans : {self.venv_dir}")
            subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_dir)],
                check=True
            )
            self.print_success("Environnement virtuel créé")
            return True
        
        except subprocess.CalledProcessError as e:
            self.print_error(f"Échec de la création du venv : {e}")
            return False
    
    def get_venv_python(self):
        """Retourne le chemin vers Python dans le venv."""
        if platform.system() == "Windows":
            return self.venv_dir / "Scripts" / "python.exe"
        else:
            return self.venv_dir / "bin" / "python"
    
    def get_venv_pip(self):
        """Retourne le chemin vers pip dans le venv."""
        if platform.system() == "Windows":
            return self.venv_dir / "Scripts" / "pip.exe"
        else:
            return self.venv_dir / "bin" / "pip"
    
    def upgrade_pip(self):
        """Met à jour pip dans le venv."""
        self.print_step(4, "Mise à jour de pip dans le venv")
        
        venv_pip = self.get_venv_pip()
        
        try:
            subprocess.run(
                [str(venv_pip), "install", "--upgrade", "pip"],
                check=True,
                capture_output=True
            )
            self.print_success("pip mis à jour")
            return True
        
        except subprocess.CalledProcessError:
            self.print_warning("Échec de la mise à jour de pip (non critique)")
            return True
    
    def install_requirements(self):
        """Installe les dépendances Python."""
        self.print_step(5, "Installation des dépendances Python")
        
        venv_pip = self.get_venv_pip()
        
        # Vérifier requirements.txt
        if not self.requirements_file.exists():
            self.print_warning("requirements.txt non trouvé")
            self.print_info("Installation manuelle de Flask et Pydantic...")
            
            try:
                subprocess.run(
                    [str(venv_pip), "install", "flask>=3.0.0", "pydantic>=2.0.0"],
                    check=True
                )
                self.print_success("Flask et Pydantic installés")
                return True
            
            except subprocess.CalledProcessError as e:
                self.print_error(f"Échec de l'installation : {e}")
                return False
        
        # Installer depuis requirements.txt
        self.print_info(f"Installation depuis : {self.requirements_file}")
        
        try:
            subprocess.run(
                [str(venv_pip), "install", "-r", str(self.requirements_file)],
                check=True
            )
            self.print_success("Dépendances installées")
            return True
        
        except subprocess.CalledProcessError as e:
            self.print_error(f"Échec de l'installation : {e}")
            return False
    
    def verify_installation(self):
        """Vérifie que Flask et Pydantic sont installés."""
        self.print_step(6, "Vérification de l'installation")
        
        venv_python = self.get_venv_python()
        
        # Vérifier Flask
        try:
            result = subprocess.run(
                [str(venv_python), "-c", "import flask; print(flask.__version__)"],
                capture_output=True,
                text=True,
                check=True
            )
            flask_version = result.stdout.strip()
            self.print_success(f"Flask {flask_version} installé")
        
        except subprocess.CalledProcessError:
            self.print_error("Flask non installé")
            return False
        
        # Vérifier Pydantic
        try:
            result = subprocess.run(
                [str(venv_python), "-c", "import pydantic; print(pydantic.__version__)"],
                capture_output=True,
                text=True,
                check=True
            )
            pydantic_version = result.stdout.strip()
            self.print_success(f"Pydantic {pydantic_version} installé")
        
        except subprocess.CalledProcessError:
            self.print_error("Pydantic non installé")
            return False
        
        return True
    
    def launch_application(self):
        """Lance l'application Flask."""
        self.print_step(7, "Lancement de l'application")
        
        venv_python = self.get_venv_python()
        web_app = self.project_dir / "web_app.py"
        
        if not web_app.exists():
            self.print_error(f"Fichier non trouvé : {web_app}")
            return False
        
        self.print_info("Démarrage du serveur Flask...")
        self.print_info("URL : http://localhost:5000")
        self.print_info("Arrêt : CTRL+C")
        print()
        
        # Ouvrir le navigateur après 2 secondes
        def open_browser():
            time.sleep(2)
            self.print_info("Ouverture du navigateur...")
            webbrowser.open("http://localhost:5000")
        
        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Lancer Flask
        try:
            subprocess.run(
                [str(venv_python), str(web_app)],
                cwd=str(self.project_dir)
            )
        
        except KeyboardInterrupt:
            print("\n")
            self.print_success("Application arrêtée")
        
        except Exception as e:
            self.print_error(f"Erreur lors du lancement : {e}")
            return False
        
        return True
    
    def run(self):
        """Exécute l'installation et le lancement complet."""
        self.print_header("MintyForge - Installation et Lancement")
        
        print("\nCe script va :")
        print("  1. Vérifier Python et les dépendances système")
        print("  2. Créer un environnement virtuel (.venv)")
        print("  3. Installer Flask et Pydantic")
        print("  4. Lancer l'application web")
        print("  5. Ouvrir votre navigateur automatiquement")
        print()
        
        # Étapes d'installation
        if not self.check_python_version():
            return 1
        
        if not self.check_system_dependencies():
            return 1
        
        if not self.create_venv():
            return 1
        
        if not self.upgrade_pip():
            return 1
        
        if not self.install_requirements():
            return 1
        
        if not self.verify_installation():
            return 1
        
        # Lancement
        self.print_header("Installation terminée !")
        print()
        self.print_success("MintyForge est prêt à être utilisé")
        print()
        
        response = input("❓ Voulez-vous lancer l'application maintenant ? (O/n) : ")
        
        if response.lower() not in ('n', 'non', 'no'):
            if not self.launch_application():
                return 1
        else:
            print()
            self.print_info("Pour lancer l'application plus tard :")
            print(f"  source {self.venv_dir}/bin/activate")
            print(f"  python web_app.py")
            print()
            self.print_info("Ou utilisez le script de lancement :")
            print("  python run.py")
            print()
        
        return 0


def main():
    """Point d'entrée principal."""
    try:
        setup = MintyForgeSetup()
        return setup.run()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation interrompue par l'utilisateur")
        return 1
    
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
