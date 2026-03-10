# MintyForge

Utilitaire de post-installation pour **Linux Mint 22 (Cinnamon)**. Configure rapidement une machine de façon reproductible via une interface web locale.

---

## Lancement

```bash
git clone https://github.com/ton-compte/minty_forge.git
cd minty_forge
chmod +x mintyforge.sh
./mintyforge.sh
```

Le script gère tout automatiquement :
1. Installe **uv** (gestionnaire Python rapide) si absent
2. Synchronise les dépendances via `uv sync` (Flask, Pydantic)
3. Installe `crudini` et `sassc` si absents
4. Configure les sudoers pour `ufw` et `crudini`
5. Désactive la mise en veille et le verrouillage écran
6. Lance Flask et ouvre `http://localhost:5000`

**Arrêt :** `CTRL+C` — la veille est restaurée automatiquement.

---

## Prérequis

- Linux Mint 22 / Ubuntu 24.04 avec Cinnamon
- Python 3.10+
- `curl` et `sudo`
- Accès internet (premier lancement uniquement)

---

## Fonctionnalités

### Profils d'installation

Sélectionnez un ou plusieurs profils, lancez un **dry-run** pour prévisualiser, puis installez. Chaque profil peut être personnalisé paquet par paquet via le bouton "Detail".

| Profil | Contenu |
|---|---|
| **Base** | Outils essentiels, polices, codecs, sassc, crudini |
| **Bureautique** | Thunderbird, pdfarranger, OnlyOffice (flatpak) |
| **Gaming** | Steam, gamemode, Heroic, Bottles, ProtonPlus, RetroDECK |
| **Dev** | build-essential, git, gdb, strace, meld |
| **Multimedia** | mpv, celluloid, yt-dlp, OBS (flatpak), GIMP (flatpak) |
| **Docker & Virtualisation** | Docker CE, virt-manager, KVM/QEMU |
| **Distrobox** | distrobox, podman, BoxBuddy (flatpak) |
| **AMD GPU** | Mesa Vulkan, VA-API, radeontop, corectrl |
| **NVIDIA GPU** | Mesa Vulkan, nvtop, mintdrivers |
| **Privacy** | gufw, clamtk, wireguard |
| **VPN & Réseau** | Plugins NetworkManager (L2TP, OpenConnect, WireGuard…) |
| **Navigateurs** | Chromium, Brave (dépôt officiel) |
| **Système** | gparted, timeshift, kdeconnect, scrcpy, blueman |

Le profil GPU opposé au matériel détecté est affiché avec un cadenas — l'utilisateur peut forcer l'installation après confirmation.

### Catalogue de thèmes

Installez des thèmes GTK, icônes et curseurs depuis GitHub directement dans `/usr/share/` (accessible au greeter LightDM et à tous les utilisateurs). Détection automatique des thèmes déjà installés.

Thèmes disponibles : Qogir-Light/Dark, WhiteSur, Vimix, Tela, Papirus, WhiteSur Icons, Oreo Cursors…

### Paramètres du bureau

Configure les thèmes, mode clair/sombre, polices, espaces de travail, veilleuse nocturne, veille, icônes du bureau et plus — via `gsettings` directement, sans fichiers intermédiaires.

Le **toggle Mode sombre** change simultanément `color-scheme` et le thème GTK vers sa variante sombre/claire.

### Écran de connexion (slick-greeter)

Synchronise le thème GTK, icônes, curseur, police et numlock vers `/etc/lightdm/slick-greeter.conf` via `crudini`. Les thèmes doivent être installés dans `/usr/share/` (install système).

### Pare-feu

Activation/désactivation de `ufw` via l'interface, sans mot de passe sudo.

### Historique et rollback

Chaque action est enregistrée dans `data/state.json`. Annulez la dernière action ou toutes les actions depuis l'interface.

---

## Structure du projet

```
minty_forge/
├── mintyforge.sh            # Script tout-en-un (uv, crudini, sassc, sudo, veille)
├── minty_forge.py           # Vérification environnement + lanceur Flask
├── web_app.py               # Application Flask (blueprints)
├── pyproject.toml           # Dépendances Python (uv)
├── uv.lock                  # Lock file reproductible
├── routes/
│   ├── shared.py            # État partagé : logs SSE, task lock
│   ├── legacy.py            # /api/status, /api/logs, /api/execute, /api/task
│   ├── profiles.py          # /api/profiles — installation par profil
│   ├── dconf.py             # /api/dconf — paramètres gsettings + mode sombre
│   ├── themes.py            # /api/themes — catalogue et installation de thèmes
│   ├── greeter.py           # /api/greeter — configuration slick-greeter
│   ├── system.py            # /api/system — pare-feu ufw
│   └── state_routes.py      # /api/state — historique + rollback
├── utils/
│   ├── state_manager.py     # Persistance des actions + rollback
│   ├── theme_manager.py     # Détection et installation de thèmes
│   ├── profile_loader.py    # Chargement des profils JSON
│   ├── subprocess_utils.py  # Exécution sécurisée de commandes
│   ├── file_utils.py        # JSON et gestion de fichiers
│   └── validation.py        # Validation Pydantic des configs
├── schemas/                 # Modèles Pydantic (packages, profils, thèmes…)
├── scripts/
│   └── profile_install.py   # Installation d'un profil (APT + Flatpak + External)
├── configs/
│   ├── profiles/            # Profils d'installation (*.json)
│   ├── themes_gtk.json      # Catalogue thèmes GTK
│   ├── themes_icons.json    # Catalogue thèmes icônes
│   └── themes_cursors.json  # Catalogue thèmes curseurs
├── web/
│   ├── templates/
│   │   └── index.html       # Interface HTML
│   └── static/
│       ├── css/style.css    # Styles (thème clair/sombre)
│       └── js/app.js        # JavaScript (vanilla, sans framework)
├── data/
│   └── state.json           # Historique des actions (créé automatiquement)
└── logs/
    └── mintyforge.log
```

---

## Ajouter un profil personnalisé

Créez `configs/profiles/mon_profil.json` :

```json
{
  "name": "Mon Profil",
  "description": "Description courte",
  "icon": "wrench",
  "apt": [
    { "name": "nom-paquet", "description": "Description" }
  ],
  "flatpak": [
    { "app": "com.example.App", "description": "Description" }
  ],
  "external": [
    { "name": "MonLogiciel", "description": "Description", "cmd": "commande bash" }
  ],
  "remove": [
    { "name": "paquet-a-supprimer", "description": "Description" }
  ]
}
```

Icônes disponibles : `box` `wrench` `gamepad` `cpu` `gpu` `code` `film` `shield` `server` `docker` `office`

Le profil apparaît automatiquement sans redémarrer le serveur.

---

## API

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/status` | État système (internet, sudo, disque, outils) |
| GET | `/api/logs/stream` | Logs en temps réel (SSE) |
| GET | `/api/logs/history` | Dernières 300 lignes du log |
| POST | `/api/task/cancel` | Annuler la tâche en cours |
| GET | `/api/profiles` | Liste des profils (avec détection GPU) |
| POST | `/api/profiles/install` | Installer des profils complets |
| POST | `/api/profiles/install-custom` | Installer une sélection de paquets |
| POST | `/api/profiles/dry-run` | Prévisualiser une installation |
| GET | `/api/themes/catalog` | Catalogue thèmes avec statut installé |
| POST | `/api/themes/install` | Installer un thème depuis git |
| GET | `/api/dconf/options` | Thèmes installés + paramètres actuels |
| POST | `/api/dconf/apply` | Appliquer des paramètres via gsettings |
| POST | `/api/dconf/dark-mode` | Basculer mode sombre/clair (theme + color-scheme) |
| GET | `/api/greeter/status` | Configuration slick-greeter actuelle |
| POST | `/api/greeter/sync` | Synchroniser greeter depuis le bureau |
| GET | `/api/system/firewall` | État du pare-feu ufw |
| POST | `/api/system/firewall/enable` | Activer ufw |
| POST | `/api/system/firewall/disable` | Désactiver ufw |
| GET | `/api/state` | Historique des actions |
| POST | `/api/state/rollback/last` | Annuler la dernière action |
| POST | `/api/state/rollback/all` | Annuler toutes les actions |

---

## Dépendances

**Python** (gérées par `uv sync`) :
- [Flask](https://flask.palletsprojects.com/) >= 3.0
- [Pydantic](https://docs.pydantic.dev/) >= 2.0

**Système** (installées automatiquement par `mintyforge.sh`) :
- `uv` — gestionnaire Python
- `crudini` — édition fichiers INI (slick-greeter)
- `sassc` — compilation thèmes GTK (SCSS)

---

## Licence

MIT
