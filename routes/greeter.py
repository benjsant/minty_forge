"""Routes /api/greeter - configuration slick-greeter via crudini."""
import subprocess
from pathlib import Path
from flask import Blueprint, jsonify, request

from routes.shared import log_info, log_success, log_warn

bp = Blueprint("greeter", __name__)

_CONF    = "/etc/lightdm/slick-greeter.conf"
_SECTION = "Greeter"

# Chemins systeme uniquement — lightdm ne peut pas lire ~/.themes
_SYSTEM_THEME_DIRS = [Path("/usr/share/themes"), Path("/usr/share/icons")]

# Correspondance cle greeter → (schema gsettings, cle gsettings)
_GREETER_MAP = {
    "theme-name":        ("org.cinnamon.desktop.interface", "gtk-theme"),
    "icon-theme-name":   ("org.cinnamon.desktop.interface", "icon-theme"),
    "cursor-theme-name": ("org.cinnamon.desktop.interface", "cursor-theme"),
    "font-name":         ("org.gnome.desktop.interface",    "font-name"),
}


def _crudini(args, timeout=5):
    r = subprocess.run(["sudo", "-n", "crudini"] + args,
                       capture_output=True, text=True, timeout=timeout)
    return r.returncode == 0, r.stdout.strip(), r.stderr.strip()


def _gs_get(schema, key):
    try:
        r = subprocess.run(["gsettings", "get", schema, key],
                           capture_output=True, text=True, timeout=3)
        return r.stdout.strip().strip("'") if r.returncode == 0 else ""
    except Exception:
        return ""


def _greeter_get(key):
    ok, out, _ = _crudini(["--get", _CONF, _SECTION, key])
    return out if ok else ""


def _greeter_set(key, value):
    ok, _, err = _crudini(["--set", _CONF, _SECTION, key, str(value)])
    return ok, err


def _theme_in_system(name: str) -> bool:
    """Verifie si le theme/icone est installe dans /usr/share/ (accessible par lightdm)."""
    for base in _SYSTEM_THEME_DIRS:
        if (base / name).exists():
            return True
    return False


def _resolve_system_theme(name: str) -> tuple[str, bool]:
    """Retourne (nom_a_utiliser, est_dans_system).
    Si le theme n'est pas dans /usr/share, tente le nom de base (sans suffixe -Light/-Dark).
    """
    if _theme_in_system(name):
        return name, True
    # Essayer sans suffixe Light/Dark (ex: Tela-light → Tela)
    for suffix in ("-light", "-Light", "-dark", "-Dark"):
        if name.endswith(suffix):
            base = name[:-len(suffix)]
            if _theme_in_system(base):
                return base, True
    return name, False


@bp.route('/api/greeter/status')
def greeter_status():
    """Lit la configuration actuelle de slick-greeter."""
    try:
        current = {}
        for key in list(_GREETER_MAP.keys()) + ["activate-numlock", "background"]:
            current[key] = _greeter_get(key)
        return jsonify({"success": True, "current": current})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/greeter/sync', methods=['POST'])
def greeter_sync():
    """Synchronise slick-greeter depuis les reglages du bureau courant."""
    applied, errors, warnings = [], [], []

    # Themes/icones/curseur/police depuis gsettings
    for greeter_key, (schema, gs_key) in _GREETER_MAP.items():
        value = _gs_get(schema, gs_key)
        if not value:
            continue

        # Pour les themes visuels, verifier qu'ils sont dans /usr/share/
        if greeter_key in ("theme-name", "icon-theme-name", "cursor-theme-name"):
            resolved, in_system = _resolve_system_theme(value)
            if not in_system:
                msg = f"{value} absent de /usr/share/ — installez-le en mode systeme d'abord"
                log_warn(f"Greeter : {msg}")
                warnings.append(msg)
                continue
            if resolved != value:
                log_info(f"Greeter : {value} → {resolved} (variante systeme trouvee)")
                value = resolved

        ok, err = _greeter_set(greeter_key, value)
        if ok:
            log_info(f"Greeter : {greeter_key} = {value}")
            applied.append(f"{greeter_key} = {value}")
        else:
            log_warn(f"Greeter echec {greeter_key} : {err}")
            errors.append(greeter_key)

    # Numlock — cle correcte : activate-numlock
    ok, err = _greeter_set("activate-numlock", "true")
    if ok:
        log_info("Greeter : activate-numlock = true")
        applied.append("activate-numlock = true")
    else:
        errors.append("activate-numlock")

    if errors:
        log_warn(f"Greeter : {len(applied)} OK, {len(errors)} erreur(s)")
    else:
        log_success(f"Greeter synchronise ({len(applied)} parametres)")

    return jsonify({
        "success": len(applied) > 0,
        "applied": applied,
        "errors": errors,
        "warnings": warnings,
    })
