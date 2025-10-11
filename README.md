# 🛠️ MintyForge

**MintyForge** est un utilitaire d'automatisation pour Linux Mint (Cinnamon) — un petit "forge" personnel qui propose un menu interactif (curses) pour :

- installer une liste de paquets APT (ou tous d'un coup),
- supprimer des paquets indésirables,
- installer des Flatpaks,
- installer et configurer thèmes utilisateur (GTK / icônes / curseurs) via JSON,
- configurer Qt (kvantum / qt5ct / qt6ct),
- lancer `mintdrivers`,
- cloner/exécuter **Distroscript**,
- installer paquets externes (VirtualBox, Distrobox, Podman, etc.) via `external_packages.json`.

Le projet vise l'automatisation reproductible pour configurer rapidement une machine Mint.

---

## Sommaire

- [Prérequis](#prérequis)  
- [Arborescence du projet](#arborescence-du-projet)  
- [Installation & exécution](#installation--exécution)  
- [Fichiers de configuration (JSON / templates)](#fichiers-de-configuration-json--templates)  
- [Comportement des scripts principaux](#comportement-des-scripts-principaux)  
- [Détails techniques importants](#détails-techniques-importants)  
- [Dépannage & logs](#dépannage--logs)  
- [Sécurité & bonnes pratiques](#sécurité--bonnes-pratiques)  
- [Contribution](#contribution)  
- [Licence](#licence)

---

## Prérequis

- Système : **Linux Mint (Cinnamon)** ou distrib basée sur Ubuntu (tests ciblés Mint/Ubuntu).
- Python 3.10+ (ou 3.8+ fonctionne).
- `git`, `curl`, `gpg`, `bash`, `sudo`.
- Pour certaines actions : `crudini`, `dconf`, `gsettings` (installés par défaut sur Mint).
- Accès `sudo` pour les actions système (installation APT, copy dans `/usr/share`, modification de `/etc`).

---

## Arborescence du projet (exemple)

```
minty_forge/
├── README.md
├── minty_forge.py                # script principal (menu curses)
├── scripts/
│   ├── apt_install.py
│   ├── apt_remove.py
│   ├── flatpak_install.py
│   ├── themes_install.py
│   ├── qt_install.py
│   ├── drivers (shell)
│   ├── distroscript_install.py
│   └── external_install.py
├── configs/
│   ├── install.json              # liste APT à installer
│   ├── remove.json               # liste APT à supprimer
│   ├── flatpak.json              # liste Flatpaks
│   ├── themes_gtk.json
│   ├── themes_icons.json
│   ├── themes_cursors.json
│   ├── dconf_base                # snapshot dconf de base (template)
│   └── slick-greeter.conf        # template facultatif pour lightdm greeter
├── themes/                       # clonage local des themes GTK
├── icons/                        # clonage local des icon themes
├── cursors/                      # clonage local des cursor themes
└── logs/
    └── mintyforge.log            # logs d'exécution
```

---

## Installation & exécution

1. **Cloner le repo**

```bash
git clone https://github.com/<ton-compte>/minty_forge.git
cd minty_forge
```

2. **Lancer le menu principal**

```bash
python3 minty_forge.py
```

- Navigue avec `↑` / `↓`, `Entrée` pour lancer une action, `q` pour quitter.
- Chaque option exécute un script de `scripts/` (Python ou shell). Le menu sort proprement de curses, exécute le script (affiche la sortie) puis réinitialise le menu.

---

## Fichiers de configuration (exemples & format)

Tous les fichiers JSON sont stockés dans `configs/`. Les scripts les lisent pour déterminer les actions.

### `configs/install.json` (APT install)

```json
{
  "packages": [
    { "name": "build-essential", "description": "Essential compilation tools" },
    { "name": "git", "description": "Version control" },
    { "name": "curl", "description": "Downloader" },
    { "name": "wget", "description": "Downloader" }
  ]
}
```

### `configs/remove.json`

```json
{
  "packages": [
    { "name": "mintwelcome", "description": "Linux Mint welcome" },
    { "name": "transmission-*", "description": "Transmission client" }
  ]
}
```

### `configs/flatpak.json`

```json
{
  "flatpaks": [
    { "source": "flathub", "app": "com.github.tchx84.Flatseal", "description": "Permission manager" }
  ]
}
```

### `configs/themes_gtk.json`

```json
{
  "themes": [
    {
      "name": "Qogir-Dark",
      "name_to_use": "Qogir-Dark",
      "url": "https://github.com/vinceliuice/Qogir-theme.git",
      "cmd_user": "bash install.sh -d ~/.themes -c dark",
      "cmd_root": "bash install.sh -d /usr/share/themes -c dark",
      "description": "Qogir dark GTK theme"
    }
  ]
}
```

### `configs/external_packages.json`

```json
{
  "external_packages": [
    {
      "name": "VirtualBox 7.1",
      "description": "Oracle VirtualBox via repo Oracle",
      "cmd": "sudo bash -c 'wget -O- https://www.virtualbox.org/download/oracle_vbox_2016.asc | gpg --dearmor -o /usr/share/keyrings/oracle-virtualbox-2016.gpg && . /etc/os-release && CODENAME=${UBUNTU_CODENAME:-$VERSION_CODENAME} && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/oracle-virtualbox-2016.gpg] http://download.virtualbox.org/virtualbox/debian ${CODENAME} contrib" > /etc/apt/sources.list.d/virtualbox.list && apt update && apt install -y virtualbox-7.1 && usermod -aG vboxusers $SUDO_USER'"
    }
  ]
}
```

---

## Licence

Ce projet est sous **MIT License**.