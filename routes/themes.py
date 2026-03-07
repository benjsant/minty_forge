"""Routes /api/themes - catalogue et installation de themes depuis git."""
import json
import threading
from pathlib import Path

from flask import Blueprint, jsonify, request

from utils.theme_manager import ThemeManager
from routes.shared import (
    log_info, log_success, log_warn, log_error,
    current_task, task_lock, update_task_status
)

bp = Blueprint("themes", __name__)

_CATALOG_FILES = {
    "gtk":    "configs/themes_gtk.json",
    "icon":   "configs/themes_icons.json",
    "cursor": "configs/themes_cursors.json",
}


def _load_catalog():
    tm = ThemeManager()
    result = {}
    for theme_type, path in _CATALOG_FILES.items():
        try:
            data = json.loads(Path(path).read_text())
            entries = []
            for t in data.get("themes", []):
                installed, _ = tm.is_theme_installed(t.get("name_to_use", t["name"]), theme_type)
                entries.append({
                    "name":        t["name"],
                    "name_to_use": t.get("name_to_use", t["name"]),
                    "description": t.get("description", ""),
                    "has_url":     bool(t.get("url")),
                    "installed":   installed,
                })
            result[theme_type] = entries
        except Exception:
            result[theme_type] = []
    return result


@bp.route('/api/themes/catalog')
def themes_catalog():
    try:
        return jsonify({"success": True, "catalog": _load_catalog()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/themes/install', methods=['POST'])
def install_theme():
    data = request.get_json(silent=True) or {}
    theme_type = data.get("type")
    theme_name = data.get("name")

    if theme_type not in _CATALOG_FILES or not theme_name:
        return jsonify({"success": False, "error": "type et name requis (gtk|icon|cursor)"}), 400

    # Trouver le theme dans le catalogue
    try:
        raw = json.loads(Path(_CATALOG_FILES[theme_type]).read_text())
    except Exception:
        return jsonify({"success": False, "error": "Catalogue introuvable"}), 500

    entry = next((t for t in raw.get("themes", []) if t["name"] == theme_name), None)
    if entry is None:
        return jsonify({"success": False, "error": f"Theme '{theme_name}' introuvable"}), 404
    if not entry.get("url"):
        return jsonify({"success": False, "error": "Ce theme n'a pas d'URL git (deja inclus dans le systeme)"}), 400

    with task_lock:
        if current_task["running"]:
            return jsonify({"success": False, "error": "Tache en cours"}), 409
        current_task.update(running=True, name=f"Theme : {theme_name}", progress=0)

    def run():
        try:
            update_task_status(f"Theme : {theme_name}", True, 10)
            log_info(f"Installation du theme {theme_name}...")
            tm = ThemeManager()
            success, msg = tm.install_theme_from_git(
                entry.get("name_to_use", theme_name),
                entry["url"],
                entry.get("cmd_user", ""),
                theme_type,
            )
            if success:
                log_success(msg)
                update_task_status(f"Theme installe : {theme_name}", False, 100)
            else:
                log_error(msg)
                update_task_status(f"Echec theme : {theme_name}", False, 0)
        except Exception as e:
            log_error(f"Erreur installation theme : {e}")
            update_task_status("Erreur theme", False, 0)

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"success": True, "message": f"Installation de {theme_name} lancee"})
