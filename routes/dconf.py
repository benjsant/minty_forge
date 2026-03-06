"""Routes /api/dconf."""
import subprocess
import threading
from pathlib import Path

from flask import Blueprint, jsonify, request, Response

from utils.theme_manager import ThemeManager
from routes.shared import (
    log_info, log_success, log_error,
    current_task, task_lock, update_task_status
)

bp = Blueprint("dconf", __name__)


def _gs_get(schema, key):
    try:
        r = subprocess.run(["gsettings", "get", schema, key], capture_output=True, text=True, timeout=3)
        return r.stdout.strip().strip("'") if r.returncode == 0 else ""
    except Exception:
        return ""


def _validate_settings(settings):
    """Validation basique des settings dconf. Retourne (settings_nettoyes, erreur_ou_None)."""
    try:
        if "num_workspaces" in settings:
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

    return settings, None


def _build_changes(settings):
    """Construit le dict {section: {key: value}} depuis les settings du formulaire."""
    changes = {}

    def put(section, key, val):
        changes.setdefault(section, {})[key] = val

    for setting, dconf_key in [("gtk_theme", "gtk-theme"), ("icon_theme", "icon-theme"), ("cursor_theme", "cursor-theme")]:
        if settings.get(setting):
            v = f"'{settings[setting]}'"
            put("[org/cinnamon/desktop/interface]", dconf_key, v)
            put("[org/gnome/desktop/interface]", dconf_key, v)

    if settings.get("cinnamon_theme"):
        put("[org/cinnamon/theme]", "name", f"'{settings['cinnamon_theme']}'")
    if settings.get("wm_theme"):
        put("[org/gnome/desktop/wm/preferences]", "theme", f"'{settings['wm_theme']}'")
    if settings.get("font_name"):
        put("[org/gnome/desktop/interface]", "font-name", f"'{settings['font_name']}'")
    if settings.get("titlebar_font"):
        put("[org/gnome/desktop/wm/preferences]", "titlebar-font", f"'{settings['titlebar_font']}'")
    if settings.get("num_workspaces"):
        put("[org/gnome/desktop/wm/preferences]", "num-workspaces", settings["num_workspaces"])
    if settings.get("button_layout"):
        put("[org/gnome/desktop/wm/preferences]", "button-layout", f"'{settings['button_layout']}'")

    if "night_light_enabled" in settings:
        put("[org/cinnamon/settings-daemon/plugins/color]", "night-light-enabled", "true" if settings["night_light_enabled"] else "false")
    if settings.get("night_light_temp"):
        put("[org/cinnamon/settings-daemon/plugins/color]", "night-light-temperature", f"uint32 {settings['night_light_temp']}")

    if "lock_enabled" in settings:
        put("[org/cinnamon/desktop/screensaver]", "lock-enabled", "true" if settings["lock_enabled"] else "false")
    if "event_sounds" in settings:
        val = "true" if settings["event_sounds"] else "false"
        put("[org/cinnamon/desktop/sound]", "event-sounds", val)
        put("[org/gnome/desktop/sound]", "event-sounds", val)
    if "show_hidden_files" in settings:
        put("[org/nemo/preferences]", "show-hidden-files", "true" if settings["show_hidden_files"] else "false")

    for key in ("home", "trash", "computer"):
        if f"desktop_icons_{key}" in settings:
            put("[org/nemo/desktop]", f"{key}-icon-visible", "true" if settings[f"desktop_icons_{key}"] else "false")

    return changes


@bp.route('/api/dconf/options')
def dconf_options():
    try:
        tm = ThemeManager()
        current = {
            "gtk_theme":            _gs_get("org.cinnamon.desktop.interface", "gtk-theme"),
            "icon_theme":           _gs_get("org.cinnamon.desktop.interface", "icon-theme"),
            "cursor_theme":         _gs_get("org.cinnamon.desktop.interface", "cursor-theme"),
            "cinnamon_theme":       _gs_get("org.cinnamon.theme", "name"),
            "wm_theme":             _gs_get("org.gnome.desktop.wm.preferences", "theme"),
            "font_name":            _gs_get("org.gnome.desktop.interface", "font-name"),
            "titlebar_font":        _gs_get("org.gnome.desktop.wm.preferences", "titlebar-font"),
            "num_workspaces":       _gs_get("org.gnome.desktop.wm.preferences", "num-workspaces"),
            "button_layout":        _gs_get("org.gnome.desktop.wm.preferences", "button-layout"),
            "night_light_enabled":  _gs_get("org.cinnamon.settings-daemon.plugins.color", "night-light-enabled"),
            "night_light_temp":     _gs_get("org.cinnamon.settings-daemon.plugins.color", "night-light-temperature"),
            "lock_enabled":         _gs_get("org.cinnamon.desktop.screensaver", "lock-enabled"),
            "event_sounds":         _gs_get("org.cinnamon.desktop.sound", "event-sounds"),
            "show_hidden_files":    _gs_get("org.nemo.preferences", "show-hidden-files"),
            "desktop_icons_home":   _gs_get("org.nemo.desktop", "home-icon-visible"),
            "desktop_icons_trash":  _gs_get("org.nemo.desktop", "trash-icon-visible"),
            "desktop_icons_computer": _gs_get("org.nemo.desktop", "computer-icon-visible"),
        }
        return jsonify({
            "success": True,
            "themes": {
                "gtk": tm.list_available_themes("gtk"),
                "icon": tm.list_available_themes("icon"),
                "cursor": tm.list_available_themes("cursor"),
            },
            "current": current,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/dconf/apply', methods=['POST'])
def apply_dconf_custom():
    data = request.get_json(silent=True) or {}
    settings, err = _validate_settings(data.get("settings", {}))
    if err:
        return jsonify({"success": False, "error": err}), 400

    with task_lock:
        if current_task["running"]:
            return jsonify({"success": False, "error": "Tache en cours"}), 409
        current_task.update(running=True, name="Dconf custom", progress=0)

    def run():
        try:
            log_info("Generation de la config dconf...")
            update_task_status("Dconf custom", True, 10)

            base_path = Path("configs/dconf_base")
            if not base_path.exists():
                log_error("configs/dconf_base introuvable")
                update_task_status("Dconf echoue", False, 0)
                return

            changes = _build_changes(settings)
            lines = base_path.read_text().splitlines()
            output = []
            section = ""

            for line in lines:
                stripped = line.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    section = stripped
                    output.append(line)
                elif "=" in stripped and section in changes:
                    key = stripped.split("=", 1)[0].strip()
                    if key in changes[section]:
                        output.append(f"{key}={changes[section].pop(key)}")
                    else:
                        output.append(line)
                else:
                    output.append(line)

            for sec, keys in changes.items():
                if not keys:
                    continue
                output.append("")
                output.append(sec)
                for k, v in keys.items():
                    output.append(f"{k}={v}")

            update_task_status("Dconf custom", True, 60)

            dconf_content = "\n".join(output) + "\n"
            Path("configs/dconf_custom.dconf").write_text(dconf_content)

            update_task_status("Dconf custom", True, 80)

            # Stdin direct, pas besoin de bash ni de fichier tmp
            result = subprocess.run(
                ["dconf", "load", "/"],
                input=dconf_content,
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                log_success("Config dconf appliquee")
                update_task_status("Dconf applique", False, 100)
            else:
                log_error(f"dconf load echoue : {result.stderr}")
                update_task_status("Dconf echoue", False, 100)

        except Exception as e:
            log_error(f"Erreur dconf : {e}")
            update_task_status("Dconf echoue", False, 0)

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"success": True, "message": "Application dconf lancee"})


@bp.route('/api/dconf/export')
def export_dconf():
    try:
        r = subprocess.run(["dconf", "dump", "/"], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return jsonify({"success": False, "error": "dconf dump echoue"}), 500
        return Response(r.stdout, mimetype='text/plain',
                       headers={"Content-Disposition": "attachment; filename=dconf_export.dconf"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
