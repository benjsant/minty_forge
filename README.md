# Minty_Forge

Minty_Forge est un utilitaire de post-installation et de configuration pour **Linux Mint Cinnamon 22**.  
Il automatise la mise à jour du système, l’installation de paquets et de Flatpaks, la configuration des thèmes (GTK, icônes, curseurs), ainsi que quelques réglages système (drivers, greeter…).

---

## 🚀 Fonctionnalités

- Mise à jour du système (`apt update && apt upgrade`)
- Installation des paquets listés dans `configs/apt.txt`
- Suppression des paquets listés dans `configs/remove.txt`
- Installation des Flatpaks depuis `configs/flatpak.txt`
- Installation et configuration des thèmes :
  - GTK
  - Icônes
  - Curseurs
  - Thèmes GRUB2
- Configuration du **LightDM Slick Greeter** (`configs/slick-greeter_custom.conf`)
- Gestion des thèmes **Qt5/Qt6** via `qt5ct` et `kvantum`
- Lancement du projet **Distroscript** en option

---

## 📂 Structure du projet

```bash
mintyforge/
├── mintyforge.sh # Script principal
├── scripts/ # Scripts secondaires
│ ├── apt_install.sh
│ ├── flatpak_install.sh
│ ├── remove_packages.sh
│ ├── themes_user.sh
│ ├── themes_system.sh
│ └── distroscript_launcher.sh
├── configs/ # Fichiers de configuration
│ ├── apt.txt
│ ├── remove.txt
│ ├── flatpak.txt
│ ├── qt_themes.txt
│ └── slick-greeter_custom.conf
└── README.md
```
---

## ⚙️ Installation

Cloner le projet :

```bash
git clone https://github.com/benjsant/minty_forge.git
cd mintyforge
```
Donner les droits d’exécution aux scripts :

`chmod +x minty_forge scripts/*.sh`

## 🖥️ Utilisation

Lancer MintyForge :

```bash
./minty_forge
```

Un menu interactif vous propose :

1.  **Installation système** (paquets APT + Flatpak + suppression)
    
2.  **Installation des thèmes** (GTK, icônes, curseur)
    
3.  **Utilisation de Distroscript**
    
4.  **Quitter**
    

* * *


## 📦 Personnalisation

- Modifier les paquets APT dans `configs/apt.txt`
    
- Modifier les Flatpaks dans `configs/flatpak.txt`
    
- Modifier les suppressions dans `configs/remove.txt`
    
- Modifier la configuration du greeter dans `configs/slick-greeter_custom.conf`
    
- Modifier les thèmes Qt disponibles dans `configs/qt_themes.txt`
    

* * *

## 📜 Licence

Ce projet est distribué sous la licence **MIT**.  
Vous êtes libre de l’utiliser, le modifier et le redistribuer comme vous le souhaitez.

* * *

## 🔗 Remarques sur les licences tierces

MintyForge utilise mais **n’intègre pas** directement certains projets tiers, par exemple les thèmes et icônes de **Vinceliuice** (GPLv3) :

- [Qogir Theme](https://github.com/vinceliuice/Qogir-theme)
- [Tela Icons](https://github.com/vinceliuice/Tela-icon-theme)
- [Grub2 Themes](https://github.com/vinceliuice/grub2-themes)

Ces projets conservent leur propre licence (GPLv3).  
MintyForge ne fait que les installer via `git clone` et `install.sh`.

* * *

