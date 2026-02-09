# 🛠️ MintyForge

![minty_forge_icons](data/background.png)
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

- Système : **Linux Mint 22+ (Cinnamon)** ou distribution basée sur Ubuntu 24.04+
- Python 3.12+ (fourni par défaut avec Mint 22)
- `python3-venv` pour le virtual environment
- `git`, `curl`, `gpg`, `bash`, `sudo`
- Pour certaines actions : `crudini`, `dconf`, `gsettings` (installés par défaut sur Mint)
- Accès `sudo` pour les actions système (installation APT, copy dans `/usr/share`, modification de `/etc`)

**Note :** Le script `setup.sh` installe automatiquement `python3-venv` si nécessaire.

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

### 🌐 **Interface Web (Recommandée)**

1. **Cloner le repo**

```bash
git clone https://github.com/<ton-compte>/minty_forge.git
cd minty_forge
```

2. **Installer et configurer (une seule fois)**

```bash
chmod +x setup.sh start.sh
./setup.sh
```

Le script va :
- Vérifier Python 3.12+
- Créer un virtual environment (.venv)
- Installer Flask et les dépendances
- Tout configurer automatiquement

3. **Lancer MintyForge**

```bash
./start.sh
```

4. **Ouvrir dans votre navigateur**

```
http://localhost:5000
```

**Fonctionnalités web :**
- ✅ Interface moderne et responsive
- ✅ Gros bouton "TOUT INSTALLER"
- ✅ Actions individuelles (APT, Flatpak, Thèmes...)
- ✅ Logs en temps réel
- ✅ Barres de progression
- ✅ Accessible depuis le réseau local

Voir [INSTALL_WEB.md](INSTALL_WEB.md) pour plus de détails.

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