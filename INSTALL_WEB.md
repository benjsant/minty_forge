# 🌐 MintyForge - Interface Web

## 🚀 Installation rapide

### 1. Installation automatique (recommandée)

```bash
cd minty_forge
chmod +x setup.sh start.sh
./setup.sh
```

Le script d'installation va :
- ✅ Vérifier Python 3.12+
- ✅ Installer `python3-venv` si nécessaire
- ✅ Créer un virtual environment `.venv`
- ✅ Installer Flask et dépendances
- ✅ Tout configurer automatiquement

### 2. Lancer MintyForge

```bash
./start.sh
```

### 3. Ouvrir dans votre navigateur

```
http://localhost:5000
```

---

## ⚙️ Installation manuelle (optionnelle)

Si vous préférez installer manuellement :

```bash
# Créer le virtual environment
python3 -m venv .venv

# Activer le venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python minty_forge.py
```

---

## ✨ Fonctionnalités

- ✅ **Interface moderne** - Design responsive et élégant
- ✅ **Logs en temps réel** - Streaming live des opérations
- ✅ **Gros bouton "TOUT INSTALLER"** - Installation complète en un clic
- ✅ **Actions individuelles** - APT, Flatpak, Thèmes, etc.
- ✅ **Barres de progression** - Suivi visuel des installations
- ✅ **Status système** - Vérification Internet, Sudo, Python
- ✅ **Accessible réseau** - Utilisable depuis un autre PC

---

## 🎯 Utilisation

### Installation complète automatique

1. Cliquer sur **"🎯 TOUT INSTALLER"**
2. Confirmer
3. Regarder les logs en temps réel
4. Attendre la fin (peut prendre 10-30 minutes)

### Installation sélective

Utilisez les boutons individuels :
- 📦 **APT** - Installer paquets Debian
- 📱 **Flatpak** - Applications Flatpak
- 🎨 **Thèmes** - GTK, icônes, curseurs
- 🌐 **Externes** - VirtualBox, VSCode, Distrobox
- 🗑️ **Nettoyage** - Supprimer bloatware
- 🔧 **Drivers** - Configuration pilotes

---

## 🔧 Configuration

### Personnaliser les paquets

Éditez les fichiers JSON dans `configs/` :
- `install.json` - Paquets APT à installer
- `flatpak.json` - Applications Flatpak
- `external_packages.json` - Paquets tiers
- `themes_*.json` - Thèmes visuels

### Accès réseau local

L'interface est accessible sur le réseau :
1. Trouvez votre IP : `hostname -I`
2. Accédez depuis un autre PC : `http://<votre-ip>:5000`

---

## 🛡️ Sécurité

⚠️ **Important** :
- L'interface nécessite des droits `sudo`
- Assurez-vous que votre mot de passe sudo est en cache avant de lancer
- N'exposez pas l'interface sur Internet (localhost uniquement recommandé)

### Mettre en cache le mot de passe sudo

```bash
sudo echo "Cache sudo activé"
python3 minty_forge.py
```

---

## 📋 Prérequis

- **Python 3.12+** (fourni avec Linux Mint 22)
- **python3-venv** (installé automatiquement par setup.sh)
- **Flask** (installé automatiquement dans le venv)
- **Accès sudo** (évitez d'exécuter en root)
- **Connexion Internet**

**Note :** Sur Mint 22, tout est déjà présent par défaut !

---

## 🆚 Différences avec l'ancienne version curses

| Fonctionnalité | Curses (ancien) | Web (nouveau) |
|----------------|-----------------|---------------|
| Interface | Terminal uniquement | Navigateur moderne |
| Logs | Défilement basique | Temps réel avec auto-scroll |
| Progression | Pas de barre | Barres de progression |
| Accès réseau | ❌ | ✅ |
| Multi-device | ❌ | ✅ |
| Design | Basique | Moderne et élégant |
| Installation | Séquentielle | Tout en un clic |

---

## 🐛 Dépannage

### Flask n'est pas installé

```bash
pip3 install flask
```

### Permission refusée

```bash
sudo echo "Test"  # Cache le mot de passe sudo
python3 minty_forge.py
```

### Port 5000 déjà utilisé

Éditez `web_app.py` ligne ~300 :
```python
app.run(host='0.0.0.0', port=5001)  # Changez le port
```

### Page ne charge pas

1. Vérifiez que le serveur tourne : regardez le terminal
2. Essayez `http://127.0.0.1:5000` au lieu de localhost
3. Vérifiez votre firewall

---

## 📝 Logs

Les logs sont sauvegardés dans :
```
logs/mintyforge.log
```

---

## 🎨 Captures d'écran

L'interface comprend :
- Dashboard avec status système (Internet, Sudo, Python)
- Compteurs de paquets (APT, Flatpak, Thèmes)
- Gros bouton "TOUT INSTALLER"
- Boutons individuels pour chaque action
- Console de logs en temps réel avec auto-scroll
- Barres de progression animées

---

## 🤝 Contribution

L'interface web est construite avec :
- **Flask** (backend Python)
- **Vanilla JavaScript** (pas de framework)
- **CSS3** (design moderne sans dépendances)
- **Server-Sent Events** (streaming logs)

---

## 📄 Licence

MIT - Voir LICENSE
