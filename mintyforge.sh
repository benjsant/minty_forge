#!/bin/bash
# =============================================================
# MintyForge - Script tout-en-un
# =============================================================
# 1. Verifie Python 3 et python3-venv
# 2. Cree le venv si absent, installe les dependances
# 3. Demande le mot de passe sudo (et le garde en cache)
# 4. Desactive la mise en veille pendant l'execution
# 5. Lance l'interface web et ouvre le navigateur
# 6. Reactive la mise en veille a la fermeture
#
# Usage: ./mintyforge.sh
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
PYTHON_SCRIPT="$SCRIPT_DIR/minty_forge.py"

# -- Couleurs --
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
RESET='\033[0m'

info()    { echo -e "${BLUE}[INFO]${RESET} $1"; }
ok()      { echo -e "${GREEN}[OK]${RESET} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET} $1"; }
fail()    { echo -e "${RED}[ERREUR]${RESET} $1"; exit 1; }

echo ""
echo -e "${BLUE}================================================${RESET}"
echo -e "${GREEN}  MintyForge - Lancement complet${RESET}"
echo -e "${BLUE}================================================${RESET}"
echo ""

# =============================================================
# 1. Verifier Python 3
# =============================================================
info "Verification de Python 3..."
command -v python3 &>/dev/null || fail "Python 3 non trouve. Installez-le avec: sudo apt install python3"
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
ok "Python $PYTHON_VERSION"

# =============================================================
# 2. Verifier/installer python3-venv (avec ensurepip)
# =============================================================
if ! python3 -c "import ensurepip" 2>/dev/null; then
    warn "Module ensurepip absent, installation du paquet venv..."
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    sudo apt update -qq
    sudo apt install -y "python3.${PYTHON_MINOR}-venv"
    ok "python3.${PYTHON_MINOR}-venv installe"
fi

# =============================================================
# 3. Creer le venv si absent + installer dependances
# =============================================================
if [ ! -d "$VENV_DIR" ]; then
    info "Creation du virtual environment..."
    python3 -m venv "$VENV_DIR"
    ok "venv cree"
    NEED_INSTALL=1
elif [ ! -f "$VENV_DIR/bin/pip" ]; then
    warn "venv corrompu, recreation..."
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
    ok "venv recree"
    NEED_INSTALL=1
else
    NEED_INSTALL=0
fi

# Toujours activer le venv
source "$VENV_DIR/bin/activate"

# Installer les dependances si nouveau venv ou si requirements.txt plus recent que le venv
if [ "$NEED_INSTALL" = "1" ] || [ "$REQUIREMENTS" -nt "$VENV_DIR/installed.marker" ]; then
    info "Installation des dependances..."
    pip install --upgrade pip --quiet 2>/dev/null
    pip install -r "$REQUIREMENTS" --quiet
    touch "$VENV_DIR/installed.marker"
    ok "Dependances installees"
else
    ok "Dependances a jour"
fi

# Verification rapide de Flask
python -c "import flask" 2>/dev/null || fail "Flask non installe malgre l'installation. Verifiez requirements.txt"

# =============================================================
# 4. Demander sudo (cache le mot de passe pour les scripts)
# =============================================================
echo ""
info "Verification de l'acces sudo..."
if ! sudo -v; then
    fail "Acces sudo requis pour installer les paquets."
fi
ok "Acces sudo"

# Configurer sudoers pour ufw sans mot de passe (si pas deja fait)
SUDOERS_FILE="/etc/sudoers.d/mintyforge-ufw"
if [ ! -f "$SUDOERS_FILE" ]; then
    info "Configuration sudo pour le pare-feu (ufw)..."
    echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/ufw" | sudo tee "$SUDOERS_FILE" > /dev/null
    sudo chmod 440 "$SUDOERS_FILE"
    ok "Pare-feu configure (sudo ufw sans mot de passe)"
fi

# Garder sudo actif en arriere-plan (renouvelle toutes les 50s)
(while true; do sudo -n true 2>/dev/null; sleep 50; done) &
SUDO_KEEPER_PID=$!

# =============================================================
# 5. Desactiver la mise en veille
# =============================================================
INHIBIT_PID=""

disable_sleep() {
    # Methode 1: systemd-inhibit (ne marche qu'en wrappant un processus)
    # On utilise plutot xdg-screensaver / gsettings

    # Desactiver la mise en veille automatique via gsettings
    if command -v gsettings &>/dev/null; then
        # Sauvegarder les valeurs actuelles
        ORIG_AC_IDLE=$(gsettings get org.cinnamon.settings-daemon.plugins.power sleep-inactive-ac-timeout 2>/dev/null || echo "")
        ORIG_BAT_IDLE=$(gsettings get org.cinnamon.settings-daemon.plugins.power sleep-inactive-battery-timeout 2>/dev/null || echo "")
        ORIG_SCREENSAVER=$(gsettings get org.cinnamon.desktop.screensaver idle-activation-enabled 2>/dev/null || echo "")
        ORIG_LOCK=$(gsettings get org.cinnamon.desktop.screensaver lock-enabled 2>/dev/null || echo "")
        ORIG_DIM=$(gsettings get org.cinnamon.settings-daemon.plugins.power idle-dim 2>/dev/null || echo "")

        gsettings set org.cinnamon.settings-daemon.plugins.power sleep-inactive-ac-timeout 0 2>/dev/null
        gsettings set org.cinnamon.settings-daemon.plugins.power sleep-inactive-battery-timeout 0 2>/dev/null
        gsettings set org.cinnamon.desktop.screensaver idle-activation-enabled false 2>/dev/null
        gsettings set org.cinnamon.desktop.screensaver lock-enabled false 2>/dev/null
        gsettings set org.cinnamon.settings-daemon.plugins.power idle-dim false 2>/dev/null

        ok "Mise en veille et verrouillage desactives"
    else
        warn "gsettings non disponible, mise en veille non modifiee"
    fi

    # Methode complementaire: xdg-screensaver suspend (si disponible et X11)
    if command -v xdg-screensaver &>/dev/null && [ -n "$DISPLAY" ]; then
        # Trouver une fenetre de terminal pour inhiber le screensaver
        WID=$(xdotool getactivewindow 2>/dev/null || echo "")
        if [ -n "$WID" ]; then
            xdg-screensaver suspend "$WID" 2>/dev/null &
            INHIBIT_PID=$!
        fi
    fi
}

restore_sleep() {
    if command -v gsettings &>/dev/null; then
        [ -n "$ORIG_AC_IDLE" ]   && gsettings set org.cinnamon.settings-daemon.plugins.power sleep-inactive-ac-timeout "$ORIG_AC_IDLE" 2>/dev/null
        [ -n "$ORIG_BAT_IDLE" ]  && gsettings set org.cinnamon.settings-daemon.plugins.power sleep-inactive-battery-timeout "$ORIG_BAT_IDLE" 2>/dev/null
        [ -n "$ORIG_SCREENSAVER" ] && gsettings set org.cinnamon.desktop.screensaver idle-activation-enabled "$ORIG_SCREENSAVER" 2>/dev/null
        [ -n "$ORIG_LOCK" ]      && gsettings set org.cinnamon.desktop.screensaver lock-enabled "$ORIG_LOCK" 2>/dev/null
        [ -n "$ORIG_DIM" ]       && gsettings set org.cinnamon.settings-daemon.plugins.power idle-dim "$ORIG_DIM" 2>/dev/null
        info "Mise en veille et verrouillage restaures"
    fi
    [ -n "$INHIBIT_PID" ] && kill "$INHIBIT_PID" 2>/dev/null
}

disable_sleep

# =============================================================
# 6. Nettoyage a la fermeture (CTRL+C ou fin normale)
# =============================================================
cleanup() {
    echo ""
    info "Arret de MintyForge..."
    restore_sleep
    kill "$SUDO_KEEPER_PID" 2>/dev/null
    ok "MintyForge arrete. A bientot!"
}

trap cleanup EXIT

# =============================================================
# 7. Lancer l'application
# =============================================================
echo ""
echo -e "${BLUE}================================================${RESET}"
echo -e "${GREEN}  MintyForge pret - Lancement...${RESET}"
echo -e "${BLUE}================================================${RESET}"
echo ""
info "URL: http://localhost:5000"
info "Arret: CTRL+C"
echo ""

python "$PYTHON_SCRIPT"
