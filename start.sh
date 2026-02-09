#!/bin/bash
# Script de lancement MintyForge Web Interface
# Utilise le virtual environment Python

set -e

cd "$(dirname "$0")"

echo "================================================"
echo "🛠️  MintyForge - Interface Web"
echo "================================================"
echo ""

# Vérifier si venv existe
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment non trouvé!"
    echo "📦 Exécutez d'abord: ./setup.sh"
    exit 1
fi

# Vérifier sudo (mettre en cache le mot de passe)
echo "🔐 Vérification accès sudo..."
if sudo -v; then
    echo "✅ Accès sudo OK"
    echo ""
else
    echo "❌ Erreur : accès sudo requis"
    exit 1
fi

# Activer venv et lancer
echo "🚀 Lancement de MintyForge..."
echo ""
source .venv/bin/activate
python minty_forge.py
