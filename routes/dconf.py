"""Routes /api/dconf - parametres bureau via gsettings."""
import subprocess
import threading
from flask import Blueprint, jsonify, request, Response

from utils.theme_manager import ThemeManager
from routes.shared import (
    log_info, log_success, log_warn, log_error,
    current_task, task_lock, update_task_status
)

bp = Blueprint("dconf", __name__)

# Chaque cle de formulaire -> liste de (schema, gsettings_key)
# Certains parametres doivent etre appliques sur plusieurs schemas (cinnamon + gnome)
_SETTINGS_MAP = {
    "gtk_theme": [
        ("org.cinnamon.desktop.interface", "gtk-theme"),
        ("org.gnome.desktop.interface",    "gtk-theme"),
    ],
    "icon_theme": [
        ("org.cinnamon.desktop.interface", "icon-theme"),
        ("org.gnome.desktop.interface",    "icon-theme"),
    ],
    "cursor_theme": [
        ("org.cinnamon.desktop.interface", "cursor-theme"),
        ("org.gnome.desktop.interface",    "cursor-theme"),
    ],
    "cinnamon_theme":         [("org.cinnamon.theme",                          "name")],
    "wm_theme":               [("org.gnome.desktop.wm.preferences",            "theme")],
    "font_name":              [("org.gnome.desktop.interface",                  "font-name")],
    "titlebar_font":          [("org.gnome.desktop.wm.preferences",            "titlebar-font")],
    "button_layout":          [("org.gnome.desktop.wm.preferences",            "button-layout")],
    "num_workspaces":         [("org.gnome.desktop.wm.preferences",            "num-workspaces")],
    "night_light_enabled":    [("org.cinnamon.settings-daemon.plugins.color",  "night-light-enabled")],
    "night_light_temp":       [("org.cinnamon.settings-daemon.plugins.color",  "night-light-temperature")],
    "night_light_schedule":   [("org.cinnamon.settings-daemon.plugins.color",  "night-light-schedule-mode")],
    "lock_enabled":           [("org.cinnamon.desktop.screensaver",            "lock-enabled")],
    "idle_delay":             [("org.cinnamon.desktop.session",                "idle-delay")],
    "event_sounds": [
        ("org.cinnamon.desktop.sound", "event-sounds"),
        ("org.gnome.desktop.sound",    "event-sounds"),
    ],
    "show_hidden_files":      [("org.nemo.preferences", "show-hidden-files")],
    "desktop_icons_home":     [("org.nemo.desktop",     "home-icon-visible")],
    "desktop_icons_trash":    [("org.nemo.desktop",     "trash-icon-visible")],
    "desktop_icons_computer": [("org.nemo.desktop",     "computer-icon-visible")],
    # Veille et ecran — directement via gsettings, pas besoin de dconf
    "sleep_ac_timeout":  [("org.cinnamon.settings-daemon.plugins.power", "sleep-inactive-ac-timeout")],
    "sleep_bat_timeout": [("org.cinnamon.settings-daemon.plugins.power", "sleep-inactive-battery-timeout")],
    "screensaver_active":[("org.cinnamon.desktop.screensaver",            "idle-activation-enabled")],
    "color_scheme":      [("org.gnome.desktop.interface",                  "color-scheme")],
    "sleep_display_ac":  [("org.cinnamon.settings-daemon.plugins.power",  "sleep-display-ac")],
    "buttons_have_icons":[("org.cinnamon.settings-daemon.plugins.xsettings", "buttons-have-icons")],
    "menus_have_icons":  [("org.cinnamon.settings-daemon.plugins.xsettings", "menus-have-icons")],
    "audible_bell": [
        ("org.gnome.desktop.wm.preferences", "audible-bell"),
        ("org.cinnamon.desktop.wm.preferences", "audible-bell"),
    ],
}


def _gs_get(schema, key):
    try:
        r = subprocess.run(["gsettings", "get", schema, key],
                           capture_output=True, text=True, timeout=3)
        return r.stdout.strip().strip("'") if r.returncode == 0 else ""
    except Exception:
        return ""


def _gs_set(schema, key, value):
    try:
        # gsettings attend 'true'/'false' en minuscules pour les booleens
        if isinstance(value, bool):
            value = 'true' if value else 'false'
        elif isinstance(value, str) and value.lower() in ('true', 'false'):
            value = value.lower()
        r = subprocess.run(["gsettings", "set", schema, key, str(value)],
                           capture_output=True, text=True, timeout=5)
        return r.returncode == 0, r.stderr.strip()
    except Exception as e:
        return False, str(e)


def _validate_settings(settings):
    if "num_workspaces" in settings:
        try:
            n = int(settings["num_workspaces"])
            if not 1 <= n <= 12:
                return None, "num_workspaces doit etre entre 1 et 12"
            settings["num_workspaces"] = str(n)
        except (ValueError, TypeError):
            return None, "num_workspaces invalide"

    if "night_light_temp" in settings and settings["night_light_temp"]:
        try:
            t = int(settings["night_light_temp"])
            if not 1700 <= t <= 6500:
                return None, "night_light_temp doit etre entre 1700 et 6500"
            settings["night_light_temp"] = str(t)
        except (ValueError, TypeError):
            return None, "night_light_temp invalide"

    allowed_layouts = {":minimize,maximize,close", "close,minimize,maximize:"}
    if settings.get("button_layout") and settings["button_layout"] not in allowed_layouts:
        return None, "button_layout invalide"

    allowed_schemes = {"default", "prefer-dark"}
    if settings.get("color_scheme") and settings["color_scheme"] not in allowed_schemes:
        return None, "color_scheme invalide (valeurs: default, prefer-dark)"

    return settings, None


@bp.route('/api/dconf/options')
def dconf_options():
    try:
        tm = ThemeManager()
        current = {
            "gtk_theme":              _gs_get("org.cinnamon.desktop.interface", "gtk-theme"),
            "icon_theme":             _gs_get("org.cinnamon.desktop.interface", "icon-theme"),
            "cursor_theme":           _gs_get("org.cinnamon.desktop.interface", "cursor-theme"),
            "cinnamon_theme":         _gs_get("org.cinnamon.theme", "name"),
            "wm_theme":               _gs_get("org.gnome.desktop.wm.preferences", "theme"),
            "font_name":              _gs_get("org.gnome.desktop.interface", "font-name"),
            "titlebar_font":          _gs_get("org.gnome.desktop.wm.preferences", "titlebar-font"),
            "num_workspaces":         _gs_get("org.gnome.desktop.wm.preferences", "num-workspaces"),
            "button_layout":          _gs_get("org.gnome.desktop.wm.preferences", "button-layout"),
            "night_light_enabled":    _gs_get("org.cinnamon.settings-daemon.plugins.color", "night-light-enabled"),
            "night_light_temp":       _gs_get("org.cinnamon.settings-daemon.plugins.color", "night-light-temperature"),
            "night_light_schedule":   _gs_get("org.cinnamon.settings-daemon.plugins.color", "night-light-schedule-mode"),
            "lock_enabled":           _gs_get("org.cinnamon.desktop.screensaver", "lock-enabled"),
            "idle_delay":             _gs_get("org.cinnamon.desktop.session", "idle-delay"),
            "sleep_display_ac":       _gs_get("org.cinnamon.settings-daemon.plugins.power", "sleep-display-ac"),
            "buttons_have_icons":     _gs_get("org.cinnamon.settings-daemon.plugins.xsettings", "buttons-have-icons"),
            "menus_have_icons":       _gs_get("org.cinnamon.settings-daemon.plugins.xsettings", "menus-have-icons"),
            "audible_bell":           _gs_get("org.gnome.desktop.wm.preferences", "audible-bell"),
            "event_sounds":           _gs_get("org.cinnamon.desktop.sound", "event-sounds"),
            "show_hidden_files":      _gs_get("org.nemo.preferences", "show-hidden-files"),
            "desktop_icons_home":     _gs_get("org.nemo.desktop", "home-icon-visible"),
            "desktop_icons_trash":    _gs_get("org.nemo.desktop", "trash-icon-visible"),
            "desktop_icons_computer": _gs_get("org.nemo.desktop", "computer-icon-visible"),
            "sleep_ac_timeout":       _gs_get("org.cinnamon.settings-daemon.plugins.power", "sleep-inactive-ac-timeout"),
            "sleep_bat_timeout":      _gs_get("org.cinnamon.settings-daemon.plugins.power", "sleep-inactive-battery-timeout"),
            "screensaver_active":     _gs_get("org.cinnamon.desktop.screensaver", "idle-activation-enabled"),
            "color_scheme":           _gs_get("org.gnome.desktop.interface", "color-scheme"),
        }
        return jsonify({
            "success": True,
            "themes": {
                "gtk":    tm.list_available_themes("gtk"),
                "icon":   tm.list_available_themes("icon"),
                "cursor": tm.list_available_themes("cursor"),
            },
            "current": current,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/dconf/apply', methods=['POST'])
def apply_settings():
    data = request.get_json(silent=True) or {}
    settings, err = _validate_settings(data.get("settings", {}))
    if err:
        return jsonify({"success": False, "error": err}), 400

    with task_lock:
        if current_task["running"]:
            return jsonify({"success": False, "error": "Tache en cours"}), 409
        current_task.update(running=True, name="Parametres bureau", progress=0)

    def run():
        applied, errors = 0, []
        try:
            entries = [
                (schema, key, settings[form_key])
                for form_key, targets in _SETTINGS_MAP.items()
                if form_key in settings and settings[form_key] != ""
                for schema, key in targets
            ]
            total = max(len(entries), 1)
            for i, (schema, key, value) in enumerate(entries):
                ok, err_msg = _gs_set(schema, key, value)
                update_task_status("Parametres bureau", True, 10 + int((i / total) * 85))
                if ok:
                    log_info(f"gsettings: {key} = {value}")
                    applied += 1
                else:
                    log_warn(f"Echec gsettings {key}: {err_msg}")
                    errors.append(f"{key}: {err_msg}")

            if errors:
                log_warn(f"{applied} parametres appliques, {len(errors)} erreur(s)")
                update_task_status("Termine avec avertissements", False, 100)
            else:
                log_success(f"{applied} parametres appliques")
                update_task_status("Parametres appliques", False, 100)

        except Exception as e:
            log_error(f"Erreur application parametres : {e}")
            update_task_status("Erreur parametres", False, 0)

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"success": True, "message": "Application des parametres lancee"})


@bp.route('/api/dconf/export')
def export_dconf():
    """Export complet de la config dconf (backup uniquement)."""
    try:
        r = subprocess.run(["dconf", "dump", "/"], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return jsonify({"success": False, "error": "dconf dump echoue"}), 500
        return Response(r.stdout, mimetype='text/plain',
                        headers={"Content-Disposition": "attachment; filename=dconf_backup.dconf"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
