# MintyForge

Utilitaire de post-installation pour **Linux Mint (Cinnamon)**. Configure rapidement une machine de façon reproductible via une interface web locale.

---

## Prérequis

- Linux Mint 21+ / Ubuntu 22.04+ avec Cinnamon
- Python 3.10+ — `python3 --version`
- `python3-venv` — `sudo apt install python3-venv`
- Accès `sudo`
- `dconf` et `gsettings` (présents par défaut sur Mint)
- `flatpak` et `git` (optionnels, pour Flatpaks et thèmes)

---

## Lancement

```bash
git clone https://github.com/ton-compte/minty_forge.git
cd minty_forge
chmod +x mintyforge.sh
./mintyforge.sh
```

Le script vérifie Python, crée le virtualenv, installe Flask et Pydantic, demande le mot de passe `sudo`, désactive la mise en veille, puis ouvre automatiquement `http://localhost:5000`.

**Arrêt :** `CTRL+C`

---

## Fonctionnalités

### Profils d'installation

Sélectionnez un ou plusieurs profils, lancez un **dry-run** pour prévisualiser ce qui sera installé, puis installez en un clic.

| Profil | Contenu |
|---|---|
| **Base** | Outils essentiels, polices, codecs |
| **Office** | LibreOffice, Thunderbird, outils bureautiques |
| **Dev** | Python, Node.js, Podman, outils CLI |
| **Gaming** | Steam, Lutris, GameMode, Vulkan |
| **Multimedia** | VLC, Kdenlive, GIMP, Audacity |
| **Docker** | Docker Engine + Docker Compose |
| **AMD** | Pilotes Mesa, ROCm, outils AMD |
| **NVIDIA** | Pilotes propriétaires NVIDIA |
| **Privacy** | KeePassXC, outils VPN, Firejail |
| **System** | Outils système, monitoring, réseau |

### Paramètres dconf

Interface graphique pour configurer les thèmes GTK/icônes/curseurs, le mode clair/sombre, les espaces de travail, la lumière nocturne, le screensaver et les icônes du bureau — appliqués directement via `gsettings`.

### Historique et rollback

Chaque action installée est enregistrée dans `data/state.json`. Annulez la dernière action ou toutes les actions depuis l'interface.

---

## Structure du projet

```
minty_forge/
├── mintyforge.sh           # Lancement tout-en-un (venv + sudo + veille)
├── minty_forge.py          # Vérification de l'environnement + lanceur Flask
├── web_app.py              # Application Flask (enregistre les blueprints)
├── routes/
│   ├── shared.py           # État partagé : logs, task lock, run_script()
│   ├── legacy.py           # /api/status, /api/logs, /api/execute
│   ├── profiles.py         # /api/profiles — installation par profil
│   ├── dconf.py            # /api/dconf — paramètres Cinnamon/GNOME
│   └── state_routes.py     # /api/state — historique + rollback
├── utils/
│   ├── state_manager.py    # Persistance des actions + rollback
│   ├── theme_manager.py    # Détection et installation de thèmes
│   ├── profile_loader.py   # Chargement des profils JSON
│   ├── subprocess_utils.py # Exécution sécurisée de commandes
│   ├── file_utils.py       # JSON et gestion de fichiers
│   └── validation.py       # Validation Pydantic des configs
├── schemas/                # Modèles Pydantic (packages, profils, thèmes...)
├── scripts/                # Scripts exécutés en tâche de fond
│   ├── apt_install.py
│   ├── apt_remove.py
│   ├── flatpak_install.py
│   ├── themes_install.py
│   ├── external_install.py
│   ├── drivers.py
│   ├── distroscript_install.py
│   └── profile_install.py
├── configs/
│   ├── profiles/           # Profils d'installation (*.json)
│   ├── dconf_base          # Snapshot dconf de référence
│   ├── install.json        # Paquets APT
│   ├── remove.json         # Paquets à supprimer
│   ├── flatpak.json        # Flatpaks
│   ├── external_packages.json
│   └── themes_gtk.json / themes_icons.json / themes_cursors.json
├── web/
│   └── templates/
│       └── index.html      # Interface utilisateur
├── data/
│   └── state.json          # Historique des actions (créé automatiquement)
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
    { "name": "MonLogiciel", "description": "Description", "cmd": "commande d'installation" }
  ],
  "remove": [
    { "name": "paquet-a-supprimer", "description": "Description" }
  ]
}
```

Icônes disponibles : `box` `wrench` `gamepad` `cpu` `gpu` `code` `film` `shield` `server` `docker` `office`

Le profil apparaît automatiquement sans redémarrer le serveur (cache 60s).

---

## API

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/status` | État système (internet, sudo, outils) |
| GET | `/api/logs/stream` | Logs en temps réel (SSE) |
| POST | `/api/execute/<action>` | Lancer une action (apt_install, flatpak_install...) |
| POST | `/api/execute/all` | Tout installer en séquence |
| GET | `/api/profiles` | Liste des profils disponibles |
| POST | `/api/profiles/install` | Installer des profils |
| POST | `/api/profiles/dry-run` | Prévisualiser une installation |
| GET | `/api/dconf/options` | Thèmes et paramètres actuels |
| POST | `/api/dconf/apply` | Appliquer des paramètres dconf |
| GET | `/api/state` | Historique des actions |
| POST | `/api/state/rollback/last` | Annuler la dernière action |
| POST | `/api/state/rollback/all` | Annuler toutes les actions |

---

## Tests

```bash
source .venv/bin/activate
python tests/test_state_manager.py
python tests/test_utils.py
python tests/test_validation.py
python tests/test_security.py
python tests/test_theme_manager.py
```

---

## Dépendances Python

- [Flask](https://flask.palletsprojects.com/) >= 3.0
- [Pydantic](https://docs.pydantic.dev/) >= 2.0

---

## Licence

MIT
