# 🚀 MintyForge - Guide de Démarrage Rapide

## Installation en 3 commandes

```bash
git clone https://github.com/<votre-compte>/minty_forge.git
cd minty_forge
./setup.sh
```

## Lancement

```bash
./start.sh
```

Puis ouvrez votre navigateur : **http://localhost:5000**

---

## 🎯 Utilisation

### Installation complète (recommandée)

1. Cliquez sur le gros bouton **"🎯 TOUT INSTALLER"**
2. Confirmez
3. Regardez les logs en temps réel
4. Attendez la fin (~10-30 minutes selon votre connexion)

C'est tout ! MintyForge va :
- ✅ Mettre à jour le système APT
- ✅ Installer tous les paquets définis dans `configs/install.json`
- ✅ Installer les paquets externes (VirtualBox, VSCode, Distrobox...)
- ✅ Supprimer les bloatwares (définis dans `configs/remove.json`)
- ✅ Installer les applications Flatpak
- ✅ Installer et appliquer les thèmes GTK, icônes, curseurs
- ✅ Configurer les drivers

### Installation sélective

Utilisez les boutons individuels si vous voulez installer seulement certains éléments :

- **📦 APT** - Paquets Debian/Ubuntu
- **📱 Flatpak** - Applications Flatpak
- **🎨 Thèmes** - Thèmes visuels
- **🌐 Externes** - Paquets tiers
- **🗑️ Nettoyage** - Supprimer bloatware
- **🔧 Drivers** - Configuration drivers

---

## ⚙️ Personnalisation

### Modifier la liste des paquets à installer

Éditez `configs/install.json` :

```json
{
  "packages": [
    { "name": "firefox", "description": "Navigateur web" },
    { "name": "gimp", "description": "Éditeur d'images" }
  ]
}
```

### Ajouter des applications Flatpak

Éditez `configs/flatpak.json` :

```json
{
  "flatpaks": [
    { 
      "source": "flathub", 
      "app": "org.mozilla.firefox", 
      "description": "Firefox" 
    }
  ]
}
```

### Ajouter des paquets externes

Éditez `configs/external_packages.json` :

```json
{
  "packages": [
    {
      "name": "Mon paquet",
      "description": "Description",
      "cmd": "sudo apt install -y mon-paquet"
    }
  ]
}
```

---

## 🔧 Dépannage

### "sudo: mot de passe requis"

Mettez en cache votre mot de passe sudo avant de lancer :

```bash
sudo echo "Test"
./start.sh
```

### "Module venv introuvable"

Le script `setup.sh` l'installe normalement, mais manuellement :

```bash
sudo apt install python3-venv
```

### "Port 5000 déjà utilisé"

Modifiez le port dans `web_app.py` ligne ~300 :

```python
app.run(host='0.0.0.0', port=5001)
```

### Réinstaller complètement

```bash
rm -rf .venv
./setup.sh
```

---

## 📚 Documentation complète

- [README.md](README.md) - Documentation détaillée
- [INSTALL_WEB.md](INSTALL_WEB.md) - Guide interface web
- `logs/mintyforge.log` - Fichier de logs

---

## 🌐 Accès réseau

L'interface web est accessible depuis d'autres appareils sur votre réseau local :

1. Trouvez votre IP : `hostname -I`
2. Accédez depuis un autre PC : `http://<votre-ip>:5000`
3. Pratique pour monitorer l'installation depuis un téléphone !

---

## ⚠️ Note importante

MintyForge nécessite :
- Droits sudo actifs
- Connexion Internet
- Python 3.12+ (fourni avec Mint 22)

Ne lancez **JAMAIS** en root (`sudo python...`) !  
Utilisez toujours votre utilisateur normal avec sudo.

---

## 🎉 C'est tout !

MintyForge automatise l'installation complète de votre Linux Mint.  
Personnalisez les configs JSON et relancez à volonté !
