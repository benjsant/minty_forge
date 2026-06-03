# Changelog - MintyForge

Tous les changements notables de ce projet seront documentés dans ce fichier.

## [2.3.0] - 2026-06-03

### 🛡️ Sécurité

- **Garde Origin/Referer** sur toutes les routes mutantes (`POST`/`PUT`/`PATCH`/`DELETE`) — bloque les CSRF depuis un autre site dans le même navigateur (`web_app.py:_origin_guard`).
- **Defense in depth `/api/profiles/install-custom`** : le body JSON ne contient plus que le slug et les noms des paquets ; les commandes `external.cmd` sont résolues côté serveur depuis le profil canonique (élimine l'injection shell via body).
- **Sudoers temporaire** : `/etc/sudoers.d/mintyforge` est désormais supprimé à l'arrêt de l'app (trap `cleanup` dans `mintyforge.sh`), au lieu de persister indéfiniment.

### 🐛 Corrections

- **Rollback APT cassé** : `StateManager._execute_rollback` préfixe désormais `sudo -n` pour les commandes `apt`/`apt-get`/`dpkg`/`snap`. Les rollbacks APT étaient silencieusement inopérants.
- **Timeouts APT** : `apt_install` (30 min), `apt_remove` (10 min), `apt_update` (5 min), `apt_upgrade` (1 h), `flatpak_install` (30 min) — évite qu'un dépôt qui pendouille bloque toute la file de tâches.
- **`_status_cache` thread-safe** : ajout d'un `threading.Lock` (`routes/legacy.py`).
- **Dry-run profils** : utilise désormais le cache de profils au lieu de relire le JSON pour chaque slug.

### ✨ Nouvelles fonctionnalités

- **SSE pour la progression de tâche** : nouvelle route `/api/task/stream` qui pousse `(running, name, progress)` en temps réel. Le polling 5 s reste actif en filet de sécurité.
- **`POST /api/profiles/reload`** : invalide les caches profils/GPU sans redémarrage.
- **Bandeau batterie PC portable** : remplace l'ancienne section laptop (TLP/monitoring/dock/thermique). Refresh 30 s, code couleur dynamique (vert/orange/rouge selon charge + état AC), statut traduit en français.

### 🧪 Tests

- **`tests/test_routes.py`** : 13 smoke tests Flask (index, status, profiles, state, laptop, greeter, themes) + tests de la garde Origin et du contrat `install-custom`.

### 🗑️ Supprimé

- **Section dconf** (`routes/dconf.py`, UI, JS, CSS) — posait des problèmes d'affichage sur petits/grands écrans. Le binaire `dconf` reste utilisé par `themes_install.py`.
- **Backend laptop avancé** (TLP/monitoring/dock/thermique) : `scripts/laptop_setup.py`, `configs/laptop.json`, ~165 lignes de `routes/laptop.py`. Seul `/api/laptop/detect` subsiste pour le bandeau batterie.

### 🎨 Refactor CSS

- **Variables sémantiques** (`--success-bg`, `--warning-bg`, `--danger-bg`, `--info-bg`, `--code-bg`, etc.) avec overrides `[data-theme="dark"]` centralisés. Couleurs codées en dur éliminées des règles répétées.
- **~17 classes utilitaires** extraites des styles inline d'`index.html` (`header-actions`, `firewall-row`, `greeter-info`, `theme-tab-active`, `btn-*-outline`, etc.).

## [2.2.0] - 2026-02-07

### 🔍 Validation (Option C)

- **Validation JSON avec Pydantic** - Détection précoce des erreurs de configuration
- **Nouveau module `utils/validation.py`** - Modèles Pydantic pour tous les configs
- **Fail-fast** - Erreurs détectées au démarrage (<1s) plutôt qu'au runtime
- **Messages d'erreur clairs** - Localisation précise avec explications
- **Type hints** - Autocomplete et validation dans IDE
- **8 validateurs** - install, remove, flatpak, external, themes_gtk, themes_icons, themes_cursors, kvantum

### ✨ Nouvelles fonctionnalités

- **Validation automatique** - `load_package_list()` valide par défaut
- **Détection duplications** - Empêche packages/apps/thèmes dupliqués
- **Validation format** - URLs, Flatpak IDs, noms de packages
- **Validation cohérence** - URLs avec commandes d'installation
- **Champs stricts** - Détection de champs inconnus (`extra='forbid'`)
- **Tests complets** - `test_validation.py` avec 8 tests (100% succès)

### 🔄 Changements

- **`utils/file_utils.py`** - `load_package_list()` avec paramètre `validate=True`
- **`scripts/apt_install.py`** - Simplifié, utilise `load_package_list()`
- **`requirements.txt`** - Ajout de `pydantic>=2.0.0`
- **`utils/__init__.py`** - Exports des fonctions/modèles de validation

### 📝 Documentation

- **OPTION_C_SUMMARY.md** - Documentation complète Option C
- **Exemples d'utilisation** - Validation automatique et explicite
- **Messages d'erreur** - Exemples de détection

### ✅ Validations implémentées

- Packages APT : nom non vide, pas de duplications
- Flatpak : format app ID (com.example.App)
- Packages externes : commande d'installation requise
- Thèmes : URL valide, cohérence URL/commandes
- Kvantum : format liste racine

### 🧪 Tests

- 8 tests de validation (100% succès)
- 8 fichiers JSON validés (56 items au total)
- Rétrocompatibilité garantie

---

## [2.1.0] - 2026-02-07

### 🔧 Refactoring (Option B)

- **Module utilitaire centralisé** - Élimination code dupliqué
- **`utils/logging_utils.py`** - Logging colorisé (150 lignes)
- **`utils/file_utils.py`** - Opérations JSON/fichiers (250 lignes)
- **~530 lignes dupliquées éliminées** - Code consistant et maintenable
- **6 scripts refactorisés** - Imports propres depuis utils
- **Tests complets** - `test_utils.py` (100% succès)

---

## [2.0.0] - 2026-02-07

### 🛡️ Sécurité (CRITIQUE)

- **Élimination complète de `shell=True`** - Tous les appels subprocess.run() ont été sécurisés
- **Nouveau module `utils/subprocess_utils.py`** - Fonctions sécurisées centralisées
- **Protection contre l'injection de commandes** - Validation et parsing sécurisés
- **Tests de sécurité** - Script `test_security.py` pour validation continue

### ✨ Nouvelles fonctionnalités

- **Interface Web Flask** - Alternative moderne à l'interface curses
- **Logs en temps réel** - Streaming via Server-Sent Events dans le navigateur
- **Bouton "TOUT INSTALLER"** - Installation complète en un clic
- **Dashboard interactif** - Suivi visuel avec barres de progression
- **Accès réseau** - Interface accessible depuis d'autres appareils
- **Virtual environment** - Isolation Python avec `.venv`

### 🔄 Changements

- **Scripts refactorisés** - Tous utilisent maintenant le module `utils`
- **Meilleure gestion d'erreurs** - Objets `CommandResult` structurés
- **Code modernisé** - Python 3.12+ (Linux Mint 22)
- **Documentation améliorée** - SECURITY.md, QUICKSTART.md, INSTALL_WEB.md
- **Scripts d'installation** - `setup.sh` et `start.sh` automatisés

### 📝 Fichiers modifiés

#### Nouveaux fichiers
- `web_app.py` - Serveur Flask
- `web/templates/index.html` - Interface web
- `utils/subprocess_utils.py` - Module sécurisé
- `utils/__init__.py` - Exports du module
- `setup.sh` - Installation automatique
- `start.sh` - Lancement simplifié
- `test_security.py` - Tests de sécurité
- `SECURITY.md` - Documentation sécurité
- `QUICKSTART.md` - Guide rapide
- `INSTALL_WEB.md` - Guide interface web
- `requirements.txt` - Dépendances Python

#### Fichiers modifiés (sécurisés)
- `scripts/apt_install.py` - Utilise `utils`
- `scripts/apt_remove.py` - Utilise `utils`
- `scripts/flatpak_install.py` - Utilise `utils`
- `scripts/external_install.py` - Utilise `utils` avec `bash -c`
- `scripts/distroscript_install.py` - Utilise `utils`
- `scripts/qt_install.py` - Utilise `utils`
- `minty_forge.py` - Lance l'interface web
- `.gitignore` - Ajout de `.venv/` et fichiers Flask

### 🐛 Corrections

- **Risques d'injection** - Éliminés par l'utilisation de listes d'arguments
- **Validation manquante** - Module utils valide les commandes
- **Code dupliqué** - Fonctions centralisées dans utils

### 🗑️ Supprimé

- **Dépendance curses dans le script principal** - Remplacé par Flask
- **Appels `shell=True`** - Tous éliminés (0 occurrences)
- **Fonctions `run_cmd()` locales** - Remplacées par module utils

### ⚡ Performances

- Aucun impact négatif sur les performances
- Streaming des logs plus efficace via SSE
- Virtual environment réduit les conflits

### 📋 Compatibilité

- **Compatible** - Python 3.12+ (Linux Mint 22)
- **Rétrocompatible** - Tous les fichiers JSON de config fonctionnent
- **Migration** - Aucune action requise pour les utilisateurs

### 🧪 Tests

- **test_security.py** - Tous les tests passent ✅
- **Imports** - Validation du module utils
- **Commandes** - Test des fonctions sécurisées
- **Paquets** - Vérification d'installation

---

## [1.0.0] - Date antérieure

### Fonctionnalités initiales

- Menu curses interactif
- Installation paquets APT
- Installation Flatpak
- Configuration thèmes GTK/Icons/Cursors
- Installation paquets externes
- Support Distroscript
- Configuration Qt/Kvantum
- Logs basiques
- Fichiers de configuration JSON

---

## Légende

- 🛡️ Sécurité
- ✨ Nouvelle fonctionnalité
- 🔄 Changement
- 🐛 Correction de bug
- 🗑️ Suppression
- ⚡ Performance
- 📝 Documentation
- 🧪 Tests

## Comment interpréter le versioning

Format : `MAJOR.MINOR.PATCH`

- **MAJOR** - Changements incompatibles de l'API
- **MINOR** - Nouvelles fonctionnalités rétrocompatibles
- **PATCH** - Corrections de bugs rétrocompatibles

---

**Note :** La version 2.0.0 marque une refonte majeure de sécurité et d'interface.
