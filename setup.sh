#!/bin/bash
# Script d'installation MintyForge Web Interface
# Crée un virtual environment Python et installe les dépendances

set -e

cd "$(dirname "$0")"

echo "================================================"
echo "🛠️  MintyForge - Installation"
echo "================================================"
echo ""

# Vérifier Python 3.12+
echo "🐍 Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION détecté"
echo ""

# Vérifier/installer python3-venv
echo "📦 Vérification du module venv..."
if ! python3 -c "import venv" 2>/dev/null; then
    echo "⚠️  Module venv non trouvé, installation..."
    sudo apt update
    sudo apt install -y python3-venv
    echo "✅ python3-venv installé"
else
    echo "✅ Module venv OK"
fi
echo ""

# Supprimer ancien venv si existe
if [ -d ".venv" ]; then
    echo "♻️  Ancien venv détecté, suppression..."
    rm -rf .venv
fi

# Créer le virtual environment
echo "🔨 Création du virtual environment..."
python3 -m venv .venv
echo "✅ Virtual environment créé"
echo ""

# Activer et installer les dépendances
echo "📥 Installation des dépendances..."
source .venv/bin/activate

# Mise à jour pip
pip install --upgrade pip --quiet

# Installation des dépendances
pip install -r requirements.txt --quiet

echo "✅ Dépendances installées"
echo ""

# Vérifier Flask
if python -c "import flask" 2>/dev/null; then
    FLASK_VERSION=$(python -c "import flask; print(flask.__version__)")
    echo "✅ Flask $FLASK_VERSION installé"
else
    echo "❌ Erreur: Flask n'a pas pu être installé"
    exit 1
fi

echo ""
echo "================================================"
echo "✅ Installation terminée avec succès!"
echo "================================================"
echo ""
echo "📝 Pour lancer MintyForge :"
echo "   ./start.sh"
echo ""
echo "   Ou manuellement :"
echo "   source .venv/bin/activate"
echo "   python minty_forge.py"
echo ""
echo "🌐 L'interface sera accessible sur :"
echo "   http://localhost:5000"
echo ""
