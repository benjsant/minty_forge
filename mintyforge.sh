#!/bin/bash
# =============================================================
# MintyForge - Script tout-en-un
# =============================================================
# 1. Verifie Python 3
# 2. Installe uv si absent, puis synchronise les dependances (uv sync)
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
# 2. Verifier/installer uv
# =============================================================
if ! command -v uv &>/dev/null; then
    info "uv non trouve, installation..."
    _UV_DONE=0

    # Methode 1 : script officiel astral.sh (telecharge d'abord, execute ensuite)
    if curl -LsSf https://astral.sh/uv/install.sh -o /tmp/_uv_install.sh 2>/dev/null; then
        sh /tmp/_uv_install.sh && _UV_DONE=1
        rm -f /tmp/_uv_install.sh
    else
        warn "Script officiel astral.sh indisponible (erreur reseau), tentative via pip..."
    fi

    # Methode 2 : fallback pip
    if [ "$_UV_DONE" = "0" ]; then
        pip install --user uv --quiet 2>/dev/null \
            || pip3 install --user uv --quiet 2>/dev/null \
            || fail "Impossible d'installer uv. Essayez manuellement : pip install uv"
    fi

    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    command -v uv &>/dev/null || fail "uv introuvable apres installation (PATH: $PATH)"
    ok "uv installe ($(uv --version | cut -d' ' -f2))"
else
    ok "uv $(uv --version | cut -d' ' -f2)"
fi

# =============================================================
# 3. Synchroniser les dependances avec uv
# =============================================================
info "Synchronisation des dependances (uv sync)..."
uv sync --quiet || fail "uv sync a echoue. Verifiez pyproject.toml"
ok "Dependances synchronisees"

# Verification rapide de Flask via uv run
uv run python -c "import flask" 2>/dev/null || fail "Flask introuvable apres uv sync"

# =============================================================
# 4. Demander sudo (cache le mot de passe pour les scripts)
# =============================================================
echo ""
info "Verification de l'acces sudo..."
if ! sudo -v; then
    fail "Acces sudo requis pour installer les paquets."
fi
ok "Acces sudo"

# =============================================================
# 4b. Installer crudini et sassc si absents (requis par MintyForge)
# =============================================================
_MISSING_PKGS=()
command -v crudini &>/dev/null || _MISSING_PKGS+=("crudini")
command -v sassc   &>/dev/null || _MISSING_PKGS+=("sassc")
command -v acpi    &>/dev/null || _MISSING_PKGS+=("acpi")
if [ ${#_MISSING_PKGS[@]} -gt 0 ]; then
    info "Installation des outils requis : ${_MISSING_PKGS[*]}..."
    sudo apt install -y "${_MISSING_PKGS[@]}" -qq \
        || warn "Impossible d'installer : ${_MISSING_PKGS[*]} (verifiez la connexion)"
    ok "Outils requis installes"
fi

# Configurer sudoers pour ufw et crudini sans mot de passe (si pas deja fait)
SUDOERS_FILE="/etc/sudoers.d/mintyforge"
if [ ! -f "$SUDOERS_FILE" ]; then
    info "Configuration sudo (ufw + crudini)..."
    CRUDINI_PATH=$(command -v crudini 2>/dev/null || echo "/usr/bin/crudini")
    {
        echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/ufw"
        echo "$USER ALL=(ALL) NOPASSWD: $CRUDINI_PATH"
    } | sudo tee "$SUDOERS_FILE" > /dev/null
    sudo chmod 440 "$SUDOERS_FILE"
    ok "Sudo configure (ufw + crudini sans mot de passe)"
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
        ORIG_IDLE_DELAY=$(gsettings get org.cinnamon.desktop.session idle-delay 2>/dev/null || echo "")

        gsettings set org.cinnamon.settings-daemon.plugins.power sleep-inactive-ac-timeout 0 2>/dev/null || true
        gsettings set org.cinnamon.settings-daemon.plugins.power sleep-inactive-battery-timeout 0 2>/dev/null || true
        gsettings set org.cinnamon.desktop.screensaver idle-activation-enabled false 2>/dev/null || true
        gsettings set org.cinnamon.desktop.screensaver lock-enabled false 2>/dev/null || true
        gsettings set org.cinnamon.settings-daemon.plugins.power idle-dim false 2>/dev/null || true
        gsettings set org.cinnamon.desktop.session idle-delay 0 2>/dev/null || true

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
        [ -n "$ORIG_AC_IDLE" ]     && gsettings set org.cinnamon.settings-daemon.plugins.power sleep-inactive-ac-timeout "$ORIG_AC_IDLE" 2>/dev/null || true
        [ -n "$ORIG_BAT_IDLE" ]    && gsettings set org.cinnamon.settings-daemon.plugins.power sleep-inactive-battery-timeout "$ORIG_BAT_IDLE" 2>/dev/null || true
        [ -n "$ORIG_SCREENSAVER" ] && gsettings set org.cinnamon.desktop.screensaver idle-activation-enabled "$ORIG_SCREENSAVER" 2>/dev/null || true
        [ -n "$ORIG_LOCK" ]        && gsettings set org.cinnamon.desktop.screensaver lock-enabled "$ORIG_LOCK" 2>/dev/null || true
        [ -n "$ORIG_DIM" ]        && gsettings set org.cinnamon.settings-daemon.plugins.power idle-dim "$ORIG_DIM" 2>/dev/null || true
        [ -n "$ORIG_IDLE_DELAY" ] && gsettings set org.cinnamon.desktop.session idle-delay "$ORIG_IDLE_DELAY" 2>/dev/null || true
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

uv run python "$PYTHON_SCRIPT"
