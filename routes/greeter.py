"""Routes /api/greeter - configuration slick-greeter via crudini."""
import subprocess
from flask import Blueprint, jsonify, request

from routes.shared import log_info, log_success, log_warn, log_error

bp = Blueprint("greeter", __name__)

_CONF     = "/etc/lightdm/slick-greeter.conf"
_SECTION  = "Greeter"

# Correspondance cle greeter → cle gsettings
_GREETER_MAP = {
    "theme-name":        ("org.cinnamon.desktop.interface", "gtk-theme"),
    "icon-theme-name":   ("org.cinnamon.desktop.interface", "icon-theme"),
    "cursor-theme-name": ("org.cinnamon.desktop.interface", "cursor-theme"),
    "font-name":         ("org.gnome.desktop.interface",    "font-name"),
}


def _crudini(args, timeout=5):
    r = subprocess.run(
        ["sudo", "-n", "crudini"] + args,
        capture_output=True, text=True, timeout=timeout
    )
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


@bp.route('/api/greeter/status')
def greeter_status():
    """Lit la configuration actuelle de slick-greeter."""
    try:
        current = {}
        for key in list(_GREETER_MAP.keys()) + ["numlock", "background"]:
            current[key] = _greeter_get(key)
        return jsonify({"success": True, "current": current})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/greeter/sync', methods=['POST'])
def greeter_sync():
    """Synchronise slick-greeter depuis les reglages du bureau courant."""
    applied, errors = [], []

    # Themes/polices depuis gsettings
    for greeter_key, (schema, gs_key) in _GREETER_MAP.items():
        value = _gs_get(schema, gs_key)
        if not value:
            continue
        ok, err = _greeter_set(greeter_key, value)
        if ok:
            log_info(f"Greeter : {greeter_key} = {value}")
            applied.append(f"{greeter_key} = {value}")
        else:
            log_warn(f"Greeter echec {greeter_key} : {err}")
            errors.append(greeter_key)

    # Numlock
    ok, err = _greeter_set("numlock", "true")
    if ok:
        log_info("Greeter : numlock = true")
        applied.append("numlock = true")
    else:
        errors.append("numlock")

    if errors:
        log_warn(f"Greeter : {len(applied)} OK, {len(errors)} erreur(s) — sudo crudini disponible ?")
        return jsonify({"success": len(applied) > 0, "applied": applied, "errors": errors})

    log_success(f"Greeter synchronise ({len(applied)} parametres)")
    return jsonify({"success": True, "applied": applied})


@bp.route('/api/greeter/apply', methods=['POST'])
def greeter_apply():
    """Applique des valeurs specifiques a slick-greeter."""
    data = request.get_json(silent=True) or {}
    applied, errors = [], []

    allowed = set(list(_GREETER_MAP.keys()) + ["numlock", "background"])
    for key, value in data.items():
        if key not in allowed or not value:
            continue
        ok, err = _greeter_set(key, value)
        if ok:
            log_info(f"Greeter : {key} = {value}")
            applied.append(f"{key} = {value}")
        else:
            log_warn(f"Greeter echec {key} : {err}")
            errors.append(key)

    return jsonify({"success": len(errors) == 0, "applied": applied, "errors": errors})
