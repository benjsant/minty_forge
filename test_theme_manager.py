#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Test de la configuration des thèmes
-------------------------------------------------
Script de test pour vérifier le système de thèmes intelligent.
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from utils.theme_manager import ThemeManager


def main():
    """Test du système de thèmes."""
    
    print("="*70)
    print("🧪 Test du système de thèmes intelligent")
    print("="*70)
    print()
    
    # Créer le gestionnaire
    manager = ThemeManager()
    
    # 1. Test : Liste des thèmes disponibles
    print("📦 1. Thèmes GTK disponibles sur ce système :")
    gtk_themes = manager.list_available_themes("gtk")
    for theme in gtk_themes[:15]:
        print(f"   • {theme}")
    if len(gtk_themes) > 15:
        print(f"   ... et {len(gtk_themes) - 15} autres")
    print(f"   Total : {len(gtk_themes)} thèmes GTK\n")
    
    # 2. Test : Liste des icônes disponibles
    print("🎨 2. Thèmes d'icônes disponibles :")
    icon_themes = manager.list_available_themes("icon")
    for theme in icon_themes[:15]:
        print(f"   • {theme}")
    if len(icon_themes) > 15:
        print(f"   ... et {len(icon_themes) - 15} autres")
    print(f"   Total : {len(icon_themes)} thèmes d'icônes\n")
    
    # 3. Test : Vérification de la configuration recommandée
    config_file = Path("configs") / "theme_config_recommended.json"
    
    if not config_file.exists():
        print(f"❌ Fichier de configuration non trouvé : {config_file}")
        return 1
    
    print("🔍 3. Vérification de la configuration recommandée :")
    result = manager.check_recommended_config(config_file)
    
    print(f"   📋 Nom : {result['config_name']}")
    print(f"   📝 Description : {result['description']}")
    print()
    
    print("   Thèmes de base (système) :")
    print(f"   • GTK : {result['gtk_theme']['name']} ({result['gtk_theme']['source']})")
    print(f"   • Icônes : {result['icon_theme']['name']} ({result['icon_theme']['source']})")
    print(f"   • Curseur : {result['cursor_theme']['name']} ({result['cursor_theme']['source']})")
    print()
    
    print("   Thèmes optionnels :")
    installed_count = 0
    missing_count = 0
    
    for theme in result['optional_themes']:
        status = "✅ Installé" if theme['installed'] else "❌ Manquant"
        location = f" → {theme['path']}" if theme['installed'] else ""
        print(f"   • {theme['name']} ({theme['type']}) : {status}{location}")
        
        if theme['installed']:
            installed_count += 1
        else:
            missing_count += 1
    
    print()
    print(f"   📊 Résumé : {installed_count} installés, {missing_count} manquants")
    print()
    
    # 4. Test : Simulation d'installation (sans vraiment installer)
    if missing_count > 0:
        print("💡 4. Pour installer les thèmes manquants :")
        print("   Option A : Via l'interface web")
        print("      → Cliquez sur '🎨✨ Config Recommandée'")
        print()
        print("   Option B : Via ce script")
        print("      → python test_theme_manager.py --install")
        print()
    else:
        print("✅ 4. Tous les thèmes optionnels sont déjà installés !")
        print()
    
    # 5. Vérifier si on peut appliquer la config dconf
    print("🎨 5. Configuration dconf :")
    dconf_settings = result.get('dconf_settings', {}).get('[org/cinnamon/desktop/interface]', {})
    
    if dconf_settings:
        print("   Thèmes qui seront appliqués :")
        print(f"   • GTK : {dconf_settings.get('gtk-theme', 'N/A')}")
        print(f"   • Icônes : {dconf_settings.get('icon-theme', 'N/A')}")
        print(f"   • Curseur : {dconf_settings.get('cursor-theme', 'N/A')}")
        print()
        
        # Vérifier si les thèmes existent
        gtk_ok = manager.is_theme_installed(dconf_settings.get('gtk-theme', ''), 'gtk')[0]
        icon_ok = manager.is_theme_installed(dconf_settings.get('icon-theme', ''), 'icon')[0]
        cursor_ok = manager.is_theme_installed(dconf_settings.get('cursor-theme', ''), 'cursor')[0]
        
        if gtk_ok and icon_ok and cursor_ok:
            print("   ✅ Tous les thèmes configurés sont disponibles")
        else:
            print("   ⚠️  Certains thèmes configurés ne sont pas installés :")
            if not gtk_ok:
                print(f"      • GTK '{dconf_settings.get('gtk-theme')}' manquant")
            if not icon_ok:
                print(f"      • Icônes '{dconf_settings.get('icon-theme')}' manquant")
            if not cursor_ok:
                print(f"      • Curseur '{dconf_settings.get('cursor-theme')}' manquant")
    
    print()
    print("="*70)
    print("✅ Test terminé avec succès !")
    print("="*70)
    print()
    print("🚀 Pour tester l'application web :")
    print("   python run.py")
    print("   Puis ouvrez : http://localhost:5000")
    print()
    
    return 0


def install_missing_themes():
    """Installe les thèmes manquants."""
    manager = ThemeManager()
    config_file = Path("configs") / "theme_config_recommended.json"
    
    print("="*70)
    print("📥 Installation des thèmes manquants")
    print("="*70)
    print()
    
    success, messages = manager.apply_recommended_config(
        config_file,
        install_missing=True
    )
    
    for msg in messages:
        print(msg)
    
    print()
    if success:
        print("✅ Installation terminée avec succès !")
    else:
        print("⚠️  Installation terminée avec des erreurs")
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        sys.exit(install_missing_themes())
    else:
        sys.exit(main())
