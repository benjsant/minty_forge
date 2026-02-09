# MintyForge - Schemas Package

Modèles Pydantic pour la validation des fichiers de configuration JSON.

## 📁 Structure

```
schemas/
├── __init__.py      # Exports tous les modèles
├── packages.py      # Package, PackageList
├── flatpak.py       # FlatpakApp, FlatpakList
├── external.py      # ExternalPackage, ExternalPackageList
└── themes.py        # Theme, ThemeList, KvantumTheme, KvantumThemeList
```

## 🎯 Utilisation

### Import direct
```python
from schemas import Package, PackageList

# Créer un package
pkg = Package(name="curl", description="HTTP client")

# Valider une liste
pkg_list = PackageList(packages=[pkg])
```

### Via utils (recommandé)
```python
from utils import validate_install_config, Package

# Validation automatique
validated = validate_install_config("configs/install.json")

# Accès aux packages validés
for pkg in validated.packages:
    print(pkg.name, pkg.description)
```

## 📦 Modèles disponibles

### packages.py
- **Package** - Package APT individuel
  - `name: str` - Nom (requis, non vide)
  - `description: str` - Description (optionnel)
  
- **PackageList** - Liste de packages
  - `packages: List[Package]` - Liste (min 1 élément)
  - Validation : pas de duplications

**Utilisé par :** `install.json`, `remove.json`

---

### flatpak.py
- **FlatpakApp** - Application Flatpak
  - `source: Literal["flathub"]` - Source (défaut: "flathub")
  - `app: str` - App ID format com.example.App (requis)
  - `description: str` - Description (optionnel)
  - Validation : format reverse-DNS, min 2 parties

- **FlatpakList** - Liste d'apps Flatpak
  - `flatpaks: List[FlatpakApp]` - Liste (min 1 élément)
  - Validation : pas de duplications

**Utilisé par :** `flatpak.json`

---

### external.py
- **ExternalPackage** - Package externe
  - `name: str` - Nom (requis)
  - `description: str` - Description (optionnel)
  - `cmd: str` - Commande installation (requis)
  - Validation : commande non vide

- **ExternalPackageList** - Liste de packages externes
  - `packages: List[ExternalPackage]` - Liste (min 1 élément)

**Utilisé par :** `external_packages.json`

---

### themes.py
- **Theme** - Thème GTK/Icônes/Curseurs
  - `name: str` - Nom référence (requis)
  - `name_to_use: str` - Nom à appliquer (requis)
  - `url: str` - URL Git (optionnel, validé si présent)
  - `cmd_user: str` - Commande utilisateur (optionnel)
  - `cmd_root: str` - Commande root (optionnel)
  - `description: str` - Description (optionnel)
  - Validation : 
    - URL doit commencer par http://, https://, ou git://
    - Si URL présente → au moins cmd_user ou cmd_root requis

- **ThemeList** - Liste de thèmes
  - `themes: List[Theme]` - Liste (min 1 élément)
  - Validation : pas de duplications de noms

**Utilisé par :** `themes_gtk.json`, `themes_icons.json`, `themes_cursors.json`

---

- **KvantumTheme** - Thème Kvantum/Qt
  - `theme: str` - Nom (requis)
  - `description: str` - Description (optionnel)
  - `cmd_user: str` - Commande utilisateur (optionnel)
  - `cmd_root: str` - Commande root (optionnel)

- **KvantumThemeList** - Liste de thèmes Kvantum (RootModel)
  - `root: List[KvantumTheme]` - Liste racine (min 1 élément)
  - Format JSON : `[{...}, {...}]` (liste directe)

**Utilisé par :** `kvantum.json`

## 🔧 Validation

Toutes les validations communes :
- ✅ Pas de champs supplémentaires (extra='forbid')
- ✅ Whitespace supprimé automatiquement
- ✅ Longueurs minimales respectées
- ✅ Pas de duplications dans les listes

## 📝 Exemple : Créer un nouveau schéma

```python
# schemas/nouveau.py
from typing import List
from pydantic import BaseModel, Field, ConfigDict, field_validator

class NouveauItem(BaseModel):
    """Modèle pour un nouvel item."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='forbid'
    )
    
    name: str = Field(..., min_length=1)
    value: int = Field(ge=0, le=100)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v.startswith('_'):
            raise ValueError("Name cannot start with underscore")
        return v

class NouveauItemList(BaseModel):
    """Liste d'items."""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    items: List[NouveauItem] = Field(..., min_length=1)
```

Puis ajouter dans `__init__.py` :
```python
from .nouveau import NouveauItem, NouveauItemList

__all__ = [
    # ... autres exports
    'NouveauItem',
    'NouveauItemList',
]
```

Et dans `utils/validation.py` :
```python
from schemas import NouveauItemList

def validate_nouveau_config(path: Union[str, Path]) -> NouveauItemList:
    """Validate nouveau.json configuration."""
    return validate_config(path, NouveauItemList)
```

## 🧪 Tests

Pour tester un schéma :
```python
import pytest
from schemas.packages import Package, PackageList

def test_valid_package():
    pkg = Package(name="curl", description="Tool")
    assert pkg.name == "curl"

def test_invalid_package():
    with pytest.raises(ValidationError):
        Package(name="", description="Empty name")

def test_duplicate_detection():
    with pytest.raises(ValidationError):
        PackageList(packages=[
            Package(name="curl", description="1"),
            Package(name="curl", description="2")
        ])
```

## 📚 Documentation

Pour générer le JSON Schema d'un modèle :
```python
from schemas import Package
import json

schema = Package.model_json_schema()
print(json.dumps(schema, indent=2))
```

Résultat :
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "description": "Package name (cannot be empty)"
    },
    "description": {
      "type": "string",
      "default": "",
      "description": "Package description"
    }
  },
  "required": ["name"]
}
```

## 🚀 Avantages de cette structure

1. **Séparation des responsabilités**
   - `schemas/` = Définition des modèles Pydantic
   - `utils/validation.py` = Fonctions de validation

2. **Fichiers focalisés**
   - `packages.py` : 60 lignes (APT packages)
   - `flatpak.py` : 70 lignes (Flatpak apps)
   - `external.py` : 50 lignes (External packages)
   - `themes.py` : 160 lignes (Thèmes GTK/Icons/Cursors/Kvantum)
   - Total : ~340 lignes vs 600 lignes en un seul fichier

3. **Maintenabilité**
   - Modification d'un schéma = éditer 1 fichier ciblé
   - Ajout d'un schéma = créer 1 nouveau fichier
   - Pas de fichier monolithique

4. **Réutilisabilité**
   - Schémas importables séparément
   - Pas de dépendance aux fonctions de validation
   - Utilisable dans d'autres projets

5. **Testabilité**
   - Tester un schéma isolément
   - Tests unitaires par modèle
   - Moins de couplage

## 🔗 Voir aussi

- [utils/validation.py](../utils/validation.py) - Fonctions de validation
- [utils/file_utils.py](../utils/file_utils.py) - Intégration load_package_list()
- [test_validation.py](../test_validation.py) - Suite de tests
- [OPTION_C_SUMMARY.md](../OPTION_C_SUMMARY.md) - Documentation complète Option C
