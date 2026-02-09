# 🛠️ MintyForge - Démarrage Rapide

## 🚀 Installation et Lancement en Une Commande

```bash
python3 setup_and_run.py
```

**C'est tout !** Le script va :
1. ✅ Vérifier Python 3.8+
2. ✅ Installer les dépendances système (si nécessaire)
3. ✅ Créer l'environnement virtuel `.venv`
4. ✅ Installer Flask et Pydantic
5. ✅ Lancer l'application
6. ✅ Ouvrir votre navigateur sur http://localhost:5000

---

## 📋 Prérequis

- **Python 3.8+** (fourni avec Linux Mint 22)
- **Connexion Internet** (pour télécharger les dépendances)

### Sur Linux Mint / Ubuntu

Si `python3-venv` n'est pas installé :
```bash
sudo apt install python3-venv
```

Le script propose de l'installer automatiquement.

---

## 🎯 Utilisation

### Première Installation
```bash
python3 setup_and_run.py
```

### Lancements Suivants

**Option A : Script automatique**
```bash
python3 run.py
```

**Option B : Manuellement**
```bash
source .venv/bin/activate
python web_app.py
```

**Option C : Scripts shell (si venv créé par setup.sh)**
```bash
./start.sh
```

---

## 🎨 Fonctionnalités

### Interface Web
- **URL** : http://localhost:5000
- **Arrêt** : CTRL+C dans le terminal

### Actions Disponibles
- 📦 **APT** : Installation de packages système
- 📱 **Flatpak** : Installation d'applications Flatpak
- 🎨✨ **Config Recommandée** : Applique thèmes GTK/icônes/curseurs (intelligent)
- 🎨 **Thèmes (Avancé)** : Installation manuelle de thèmes
- 🌐 **Externes** : Packages externes (Docker, etc.)
- 🗑️ **Nettoyage** : Suppression de bloatware
- 🔧 **Drivers** : Installation de drivers

### Configuration Intelligente des Thèmes
Le bouton "🎨✨ Config Recommandée" :
- Vérifie si les thèmes sont déjà installés
- Télécharge **seulement** les thèmes manquants
- Applique la configuration via dconf
- Logs en temps réel dans l'interface

---

## 📁 Structure

```
minty_forge/
├── setup_and_run.py          # 🆕 Installation et lancement tout-en-un
├── run.py                     # Script de lancement simple
├── web_app.py                 # Serveur Flask
├── configs/                   # Configurations JSON
│   ├── install.json           # Packages APT à installer
│   ├── flatpak.json           # Applications Flatpak
│   ├── theme_config_recommended.json  # 🆕 Configuration thèmes
│   └── ...
├── utils/                     # Modules utilitaires
│   ├── theme_manager.py       # 🆕 Gestionnaire de thèmes intelligent
│   ├── validation.py          # Validation Pydantic
│   └── ...
├── schemas/                   # 🆕 Modèles Pydantic
│   ├── packages.py
│   ├── flatpak.py
│   └── ...
└── web/                       # Interface web
    ├── templates/
    └── static/
```

---

## 🧪 Tests

### Test du système de thèmes
```bash
python3 test_theme_manager.py
```

### Test de la validation
```bash
python3 test_validation.py
```

### Test de sécurité
```bash
python3 test_security.py
```

---

## 🔧 Personnalisation

### Modifier les Packages à Installer
Éditez `configs/install.json` :
```json
{
  "packages": [
    {
      "name": "git",
      "description": "Système de contrôle de version"
    }
  ]
}
```

### Modifier la Configuration des Thèmes
Éditez `configs/theme_config_recommended.json` :
```json
{
  "gtk_theme": { "name": "Mint-Y-Dark" },
  "icon_theme": { "name": "Mint-Y-Teal" },
  "cursor_theme": { "name": "DMZ-Black" }
}
```

---

## 🐛 Dépannage

### Erreur : "Module venv not found"
```bash
sudo apt install python3-venv
```

### Erreur : "Flask not installed"
```bash
source .venv/bin/activate
pip install flask pydantic
```

### Erreur : Port 5000 déjà utilisé
Modifiez le port dans `web_app.py` :
```python
app.run(host='0.0.0.0', port=5001)
```

### Logs pour Débogage
Consultez `logs/mintyforge.log`

---

## 📝 Notes

### Environnement Virtuel
Le script crée un venv dans `.venv/` pour isoler les dépendances.

### Thèmes Recommandés
- **GTK** : Mint-Y-Dark (système)
- **Icônes** : Mint-Y-Teal (système)
- **Curseur** : DMZ-Black (système)
- **Optionnels** : Qogir-Dark, WhiteSur, Tela-circle-dark (téléchargés si nécessaire)

### Sécurité
- Aucune commande n'utilise `shell=True`
- Validation Pydantic pour tous les JSON
- Execution sécurisée via `subprocess.run()`

---

## 🚀 Version

**MintyForge v2.2.0**
- ✅ Interface Web Flask
- ✅ Validation Pydantic (Option C)
- ✅ Gestionnaire de thèmes intelligent
- ✅ Architecture modulaire (schemas/)
- ✅ Logs en temps réel (SSE)

---

## 📄 Licence

MIT License - Voir [LICENSE](LICENSE)

---

## 🆘 Support

Pour toute question ou problème :
1. Consultez les logs : `logs/mintyforge.log`
2. Testez les composants : `python3 test_*.py`
3. Vérifiez les configurations : `configs/*.json`

---

**Bon déploiement ! 🎉**
