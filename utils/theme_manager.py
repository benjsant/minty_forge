#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gestion des themes : detection, installation git, application dconf."""

import json
import tempfile
from pathlib import Path

from .subprocess_utils import run_command, git_clone


class ThemeManager:
    """Detecte, installe et applique les themes GTK/icones/curseurs."""

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

    def is_theme_installed(self, theme_name, theme_type="gtk"):
        """Verifie si un theme est present. Retourne (bool, Path ou None)."""
        if theme_type == "gtk":
            search_paths = self.gtk_theme_paths
        else:
            search_paths = self.icon_theme_paths

        for base_path in search_paths:
            theme_path = base_path / theme_name
            if theme_path.exists() and theme_path.is_dir():
                if any(theme_path.iterdir()):
                    return True, theme_path

        return False, None

    def list_available_themes(self, theme_type="gtk"):
        """Liste les themes disponibles sur le systeme."""
        themes = set()

        if theme_type == "gtk":
            search_paths = self.gtk_theme_paths
        else:
            search_paths = self.icon_theme_paths

        for base_path in search_paths:
            if not base_path.exists():
                continue

            for theme_dir in base_path.iterdir():
                if theme_dir.is_dir() and not theme_dir.name.startswith('.'):
                    if theme_type == "gtk" and (theme_dir / "gtk-3.0").exists():
                        themes.add(theme_dir.name)
                    elif theme_type == "icon" and (theme_dir / "index.theme").exists():
                        themes.add(theme_dir.name)
                    elif theme_type == "cursor" and (theme_dir / "cursors").exists():
                        themes.add(theme_dir.name)

        return sorted(list(themes))

    def install_theme_from_git(self, theme_name, git_url, install_cmd, theme_type="gtk"):
        """Clone et installe un theme depuis git. Retourne (success, message)."""
        is_installed, theme_path = self.is_theme_installed(theme_name, theme_type)
        if is_installed:
            return True, f"Theme {theme_name} deja installe : {theme_path}"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            clone_path = temp_path / theme_name

            try:
                print(f"Telechargement de {theme_name}...")
                result = git_clone(git_url, clone_path, depth=1)
                if not result.success:
                    return False, f"Echec git clone : {result.stderr}"

                # install_cmd vient du JSON de config (fichier local de confiance)
                print(f"Installation de {theme_name}...")
                result = run_command(
                    ["bash", "-c", install_cmd],
                    cwd=clone_path, capture_output=True, timeout=300
                )
                if not result.success:
                    detail = (result.stderr or result.stdout or "pas de detail").strip()
                    return False, f"Echec installation : {detail}"

                is_installed, theme_path = self.is_theme_installed(theme_name, theme_type)
                if is_installed:
                    return True, f"Theme {theme_name} installe : {theme_path}"
                else:
                    return False, f"Installation terminee mais theme non trouve"

            except Exception as e:
                return False, f"Erreur : {str(e)}"

    def apply_dconf_theme(self, gtk_theme, icon_theme, cursor_theme):
        """Applique les themes via gsettings. Retourne (success, message)."""
        settings = [
            ("org.cinnamon.desktop.interface", "gtk-theme", gtk_theme),
            ("org.cinnamon.desktop.interface", "icon-theme", icon_theme),
            ("org.cinnamon.desktop.interface", "cursor-theme", cursor_theme),
        ]

        results = []
        for schema, key, value in settings:
            result = run_command(
                ["gsettings", "set", schema, key, value],
                capture_output=True, timeout=10
            )
            if result.success:
                results.append(f"OK {key}: {value}")
            else:
                results.append(f"FAIL {key}: {result.stderr}")

        ok = all(r.startswith("OK ") for r in results)
        return ok, "\n".join(results)

    def check_recommended_config(self, config_file):
        """Charge et verifie l'etat de la config recommandee."""
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

        for theme in config.get("optional_themes", []):
            is_installed, theme_path = self.is_theme_installed(theme["name"], theme["type"])
            result["optional_themes"].append({
                **theme,
                "installed": is_installed,
                "path": str(theme_path) if theme_path else None
            })

        return result

    def apply_recommended_config(self, config_file, install_missing=True):
        """Applique la config recommandee. Retourne (success, messages)."""
        messages = []

        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        messages.append(f"Configuration : {config['name']}")
        messages.append(f"{config['description']}\n")

        if install_missing:
            for theme in config.get("optional_themes", []):
                is_installed, _ = self.is_theme_installed(theme["name"], theme["type"])

                if not is_installed:
                    messages.append(f"Installation de {theme['name']}...")
                    ok, msg = self.install_theme_from_git(
                        theme["name"], theme["git_url"],
                        theme["install_cmd"], theme["type"]
                    )
                    messages.append(msg)
                else:
                    messages.append(f"{theme['name']} deja installe")

        messages.append("\nApplication des themes...")
        dconf_settings = config["dconf_settings"]["[org/cinnamon/desktop/interface]"]

        ok, msg = self.apply_dconf_theme(
            dconf_settings["gtk-theme"],
            dconf_settings["icon-theme"],
            dconf_settings["cursor-theme"]
        )
        messages.append(msg)

        return ok, messages


def main():
    """Test rapide du ThemeManager."""
    manager = ThemeManager()

    print("=" * 60)
    print("MintyForge - Theme Manager")
    print("=" * 60)
    print()

    print("Themes GTK disponibles :")
    gtk_themes = manager.list_available_themes("gtk")
    for theme in gtk_themes[:10]:
        print(f"  - {theme}")
    print(f"  ... ({len(gtk_themes)} total)")
    print()

    print("Themes d'icones disponibles :")
    icon_themes = manager.list_available_themes("icon")
    for theme in icon_themes[:10]:
        print(f"  - {theme}")
    print(f"  ... ({len(icon_themes)} total)")
    print()

    config_file = Path(__file__).parent.parent / "configs" / "theme_config_recommended.json"
    if config_file.exists():
        print("Verification configuration recommandee...")
        result = manager.check_recommended_config(config_file)
        print(f"\n{result['config_name']}")
        print(f"{result['description']}\n")
        print("Themes optionnels :")
        for theme in result["optional_themes"]:
            status = "[OK]" if theme["installed"] else "[MANQUANT]"
            print(f"  {status} {theme['name']} ({theme['type']})")
            if theme["installed"]:
                print(f"      -> {theme['path']}")
        print()

    print("=" * 60)


if __name__ == "__main__":
    main()
