#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Theme Manager
---------------------------
Gestion intelligente des thèmes :
- Vérifie si thème présent
- Télécharge et installe si nécessaire
- Applique configuration dconf
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .subprocess_utils import run_command, git_clone


class ThemeManager:
    """Gestionnaire de thèmes intelligent."""
    
    def __init__(self):
        self.gtk_theme_paths = [
            Path.home() / ".themes",
            Path("/usr/share/themes")
        ]
        self.icon_theme_paths = [
            Path.home() / ".local/share/icons",
            Path.home() / ".icons",
            Path("/usr/share/icons")
        ]
    
    def is_theme_installed(self, theme_name: str, theme_type: str = "gtk") -> Tuple[bool, Optional[Path]]:
        """
        Vérifie si un thème est déjà installé.
        
        Args:
            theme_name: Nom du thème
            theme_type: Type de thème ("gtk", "icon", "cursor")
        
        Returns:
            (bool, Path): (présent, chemin) ou (False, None)
        """
        if theme_type in ("gtk", "cursor"):
            search_paths = self.gtk_theme_paths
        else:  # icon
            search_paths = self.icon_theme_paths
        
        for base_path in search_paths:
            theme_path = base_path / theme_name
            if theme_path.exists() and theme_path.is_dir():
                # Vérifier qu'il contient des fichiers (pas juste un dossier vide)
                if any(theme_path.iterdir()):
                    return True, theme_path
        
        return False, None
    
    def list_available_themes(self, theme_type: str = "gtk") -> List[str]:
        """
        Liste tous les thèmes disponibles sur le système.
        
        Args:
            theme_type: Type de thème ("gtk", "icon", "cursor")
        
        Returns:
            Liste des noms de thèmes trouvés
        """
        themes = set()
        
        if theme_type in ("gtk", "cursor"):
            search_paths = self.gtk_theme_paths
        else:
            search_paths = self.icon_theme_paths
        
        for base_path in search_paths:
            if not base_path.exists():
                continue
            
            for theme_dir in base_path.iterdir():
                if theme_dir.is_dir() and not theme_dir.name.startswith('.'):
                    # Vérifier que c'est un vrai thème
                    if theme_type == "gtk" and (theme_dir / "gtk-3.0").exists():
                        themes.add(theme_dir.name)
                    elif theme_type == "icon" and (theme_dir / "index.theme").exists():
                        themes.add(theme_dir.name)
                    elif theme_type == "cursor" and (theme_dir / "cursors").exists():
                        themes.add(theme_dir.name)
        
        return sorted(list(themes))
    
    def install_theme_from_git(
        self,
        theme_name: str,
        git_url: str,
        install_cmd: str,
        theme_type: str = "gtk"
    ) -> Tuple[bool, str]:
        """
        Clone et installe un thème depuis git.
        
        Args:
            theme_name: Nom du thème
            git_url: URL du repository git
            install_cmd: Commande d'installation
            theme_type: Type de thème
        
        Returns:
            (success, message)
        """
        # Vérifier d'abord si déjà installé
        is_installed, theme_path = self.is_theme_installed(theme_name, theme_type)
        if is_installed:
            return True, f"✅ Thème {theme_name} déjà installé : {theme_path}"
        
        # Créer un dossier temporaire
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            clone_path = temp_path / theme_name

            try:
                # 1. Git clone
                print(f"Telechargement de {theme_name}...")
                result = git_clone(git_url, clone_path, depth=1)
                if not result.success:
                    return False, f"Echec git clone : {result.stderr}"

                # 2. Installation (install_cmd is a shell command from trusted config)
                print(f"Installation de {theme_name}...")
                result = run_command(
                    ["bash", "-c", install_cmd],
                    cwd=clone_path,
                    capture_output=True,
                    timeout=300
                )
                if not result.success:
                    return False, f"Echec installation : {result.stderr}"

                # 3. Vérifier que l'installation a réussi
                is_installed, theme_path = self.is_theme_installed(theme_name, theme_type)
                if is_installed:
                    return True, f"Theme {theme_name} installe avec succes : {theme_path}"
                else:
                    return False, f"Installation terminee mais theme non trouve"

            except Exception as e:
                return False, f"Erreur : {str(e)}"
    
    def apply_dconf_theme(
        self,
        gtk_theme: str,
        icon_theme: str,
        cursor_theme: str
    ) -> Tuple[bool, str]:
        """
        Applique les thèmes via dconf.
        
        Args:
            gtk_theme: Nom du thème GTK
            icon_theme: Nom du thème d'icônes
            cursor_theme: Nom du thème de curseur
        
        Returns:
            (success, message)
        """
        settings = [
            ("org.cinnamon.desktop.interface", "gtk-theme", gtk_theme),
            ("org.cinnamon.desktop.interface", "icon-theme", icon_theme),
            ("org.cinnamon.desktop.interface", "cursor-theme", cursor_theme),
        ]
        
        results = []
        for schema, key, value in settings:
            result = run_command(
                ["gsettings", "set", schema, key, value],
                capture_output=True,
                timeout=10
            )
            if result.success:
                results.append(f"OK {key}: {value}")
            else:
                results.append(f"FAIL {key}: {result.stderr}")
        
        success = all(r.startswith("OK ") for r in results)
        message = "\n".join(results)
        
        return success, message
    
    def check_recommended_config(self, config_file: Path) -> Dict:
        """
        Charge et vérifie la configuration recommandée.
        
        Args:
            config_file: Chemin vers theme_config_recommended.json
        
        Returns:
            Dict avec statut de chaque thème
        """
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        result = {
            "config_name": config["name"],
            "description": config["description"],
            "gtk_theme": config["gtk_theme"],
            "icon_theme": config["icon_theme"],
            "cursor_theme": config["cursor_theme"],
            "optional_themes": []
        }
        
        # Vérifier chaque thème optionnel
        for theme in config.get("optional_themes", []):
            is_installed, theme_path = self.is_theme_installed(theme["name"], theme["type"])
            theme_info = {
                **theme,
                "installed": is_installed,
                "path": str(theme_path) if theme_path else None
            }
            result["optional_themes"].append(theme_info)
        
        return result
    
    def apply_recommended_config(
        self,
        config_file: Path,
        install_missing: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Applique la configuration recommandée.
        
        Args:
            config_file: Chemin vers theme_config_recommended.json
            install_missing: Si True, installe les thèmes manquants
        
        Returns:
            (success, messages)
        """
        messages = []
        
        # Charger config
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        messages.append(f"📋 Configuration : {config['name']}")
        messages.append(f"📝 {config['description']}\n")
        
        # Vérifier et installer thèmes optionnels si demandé
        if install_missing:
            for theme in config.get("optional_themes", []):
                is_installed, _ = self.is_theme_installed(theme["name"], theme["type"])
                
                if not is_installed:
                    messages.append(f"⏳ Installation de {theme['name']}...")
                    success, msg = self.install_theme_from_git(
                        theme["name"],
                        theme["git_url"],
                        theme["install_cmd"],
                        theme["type"]
                    )
                    messages.append(msg)
                else:
                    messages.append(f"✅ {theme['name']} déjà installé")
        
        # Appliquer configuration dconf
        messages.append("\n🎨 Application des thèmes...")
        dconf_settings = config["dconf_settings"]["[org/cinnamon/desktop/interface]"]
        
        success, msg = self.apply_dconf_theme(
            dconf_settings["gtk-theme"],
            dconf_settings["icon-theme"],
            dconf_settings["cursor-theme"]
        )
        
        messages.append(msg)
        
        return success, messages


# ---------------------------------------------------------------------
# CLI pour tests
# ---------------------------------------------------------------------
def main():
    """Test CLI pour ThemeManager."""
    import sys
    
    manager = ThemeManager()
    
    print("="*60)
    print("🛠️  MintyForge - Theme Manager Test")
    print("="*60)
    print()
    
    # Lister thèmes GTK disponibles
    print("📦 Thèmes GTK disponibles :")
    gtk_themes = manager.list_available_themes("gtk")
    for theme in gtk_themes[:10]:  # Limiter à 10
        print(f"  - {theme}")
    print(f"  ... ({len(gtk_themes)} total)")
    print()
    
    # Lister thèmes d'icônes
    print("🎨 Thèmes d'icônes disponibles :")
    icon_themes = manager.list_available_themes("icon")
    for theme in icon_themes[:10]:
        print(f"  - {theme}")
    print(f"  ... ({len(icon_themes)} total)")
    print()
    
    # Tester configuration recommandée
    config_file = Path(__file__).parent.parent / "configs" / "theme_config_recommended.json"
    if config_file.exists():
        print("🔍 Vérification configuration recommandée...")
        result = manager.check_recommended_config(config_file)
        
        print(f"\n📋 {result['config_name']}")
        print(f"📝 {result['description']}\n")
        
        print("Thèmes optionnels :")
        for theme in result["optional_themes"]:
            status = "✅" if theme["installed"] else "❌"
            print(f"  {status} {theme['name']} ({theme['type']})")
            if theme["installed"]:
                print(f"      → {theme['path']}")
        print()
    
    print("="*60)


if __name__ == "__main__":
    main()
