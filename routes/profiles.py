"""Routes /api/profiles."""
import threading
import time

from flask import Blueprint, jsonify, request

from utils import (
    apt_update, apt_install, apt_remove, flatpak_install,
    check_package_installed, check_flatpak_installed, run_command,
    get_state_manager,
    ACTION_APT_INSTALL, ACTION_APT_REMOVE,
    ACTION_FLATPAK_INSTALL, ACTION_EXTERNAL_INSTALL,
)
from utils.profile_loader import load_all_profiles, get_profile
from scripts.profile_install import install_profile
from routes.shared import (
    log_info, log_success, log_warn, log_error,
    current_task, task_lock, update_task_status
)

bp = Blueprint("profiles", __name__)

PROFILE_ORDER = ["base", "office", "gaming", "dev", "multimedia", "docker", "amd", "nvidia", "privacy", "system"]

# Caches session (invalides au redemarrage seulement)
_gpu_cache = None
_profiles_cache = {"data": None, "ts": 0}
PROFILES_CACHE_TTL = 60


def _detect_gpu():
    global _gpu_cache
    if _gpu_cache is not None:
        return _gpu_cache
    try:
        import subprocess
        out = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5).stdout.lower()
        if "nvidia" in out:
            _gpu_cache = "nvidia"
        elif "amd" in out or "radeon" in out:
            _gpu_cache = "amd"
        else:
            _gpu_cache = "unknown"
    except Exception:
        _gpu_cache = "unknown"
    return _gpu_cache


def _load_profiles():
    now = time.time()
    if _profiles_cache["data"] and now - _profiles_cache["ts"] < PROFILES_CACHE_TTL:
        return _profiles_cache["data"]
    data = load_all_profiles()
    _profiles_cache["data"] = data
    _profiles_cache["ts"] = now
    return data


@bp.route('/api/profiles')
def list_profiles():
    try:
        profiles = _load_profiles()
        gpu = _detect_gpu()

        def sort_key(slug):
            try:
                return PROFILE_ORDER.index(slug)
            except ValueError:
                return len(PROFILE_ORDER)

        result = {}
        for slug in sorted(profiles.keys(), key=sort_key):
            p = profiles[slug]
            result[slug] = {
                "name": p.name,
                "description": p.description,
                "icon": p.icon,
                "suggested": slug == gpu,
                "counts": {
                    "apt": len(p.apt), "flatpak": len(p.flatpak),
                    "external": len(p.external), "remove": len(p.remove),
                    "total": p.total_packages,
                },
            }
        return jsonify({"success": True, "profiles": result, "gpu": gpu})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/profiles/<slug>')
def get_profile_detail(slug):
    profile = get_profile(slug)
    if profile is None:
        return jsonify({"success": False, "error": f"Profil '{slug}' introuvable"}), 404
    return jsonify({"success": True, "profile": profile.model_dump()})


@bp.route('/api/profiles/install', methods=['POST'])
def install_profiles():
    data = request.get_json(silent=True) or {}
    slugs = data.get("profiles", [])
    if not slugs or not isinstance(slugs, list):
        return jsonify({"success": False, "error": "Liste 'profiles' requise"}), 400
    for s in slugs:
        if get_profile(s) is None:
            return jsonify({"success": False, "error": f"Profil inconnu : {s}"}), 404

    with task_lock:
        if current_task["running"]:
            return jsonify({"success": False, "error": "Tache en cours"}), 409
        current_task.update(running=True, name=f"Profils : {', '.join(slugs)}", progress=0)

    def run():
        try:
            total = len(slugs)
            failed = []
            seen_apt, seen_flatpak, seen_external = set(), set(), set()
            log_info("apt update avant installation des profils...")
            apt_update()
            for idx, slug in enumerate(slugs):
                update_task_status(f"Profil {slug} ({idx+1}/{total})", True, int((idx / total) * 100))
                log_info(f"=== Profil : {slug} ({idx+1}/{total}) ===")
                if not install_profile(slug, seen_apt, seen_flatpak, seen_external):
                    failed.append(slug)
            if failed:
                update_task_status("Profils : erreurs", False, 100)
                log_warn(f"Profils en erreur : {', '.join(failed)}")
            else:
                update_task_status("Profils installes", False, 100)
                log_success(f"{total} profil(s) installe(s)")
        except Exception as e:
            log_error(f"Erreur installation profils : {e}")
            update_task_status("Installation echouee", False, 100)

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"success": True, "message": f"Installation : {', '.join(slugs)}"})


@bp.route('/api/profiles/dry-run', methods=['POST'])
def dry_run_profiles():
    data = request.get_json(silent=True) or {}
    slugs = data.get("profiles", [])
    if not slugs or not isinstance(slugs, list):
        return jsonify({"success": False, "error": "Liste 'profiles' requise"}), 400

    seen_apt, seen_flatpak, seen_external = set(), set(), set()
    result = {}

    for slug in slugs:
        profile = get_profile(slug)
        if profile is None:
            continue
        entry = {"apt": [], "flatpak": [], "external": [], "remove": []}

        for pkg in profile.apt:
            st = "duplicate" if pkg.name in seen_apt else ("installed" if check_package_installed(pkg.name) else "to_install")
            entry["apt"].append({"name": pkg.name, "description": pkg.description, "status": st})
            seen_apt.add(pkg.name)

        for fp in profile.flatpak:
            st = "duplicate" if fp.app in seen_flatpak else ("installed" if check_flatpak_installed(fp.app) else "to_install")
            entry["flatpak"].append({"app": fp.app, "description": fp.description, "status": st})
            seen_flatpak.add(fp.app)

        for ext in profile.external:
            st = "duplicate" if ext.name in seen_external else "to_install"
            entry["external"].append({"name": ext.name, "description": ext.description, "status": st})
            seen_external.add(ext.name)

        for pkg in profile.remove:
            st = "installed" if check_package_installed(pkg.name) else "absent"
            entry["remove"].append({"name": pkg.name, "description": pkg.description, "status": st})

        result[slug] = entry

    return jsonify({"success": True, "dry_run": result})


@bp.route('/api/profiles/install-custom', methods=['POST'])
def install_custom():
    """Installe une selection manuelle de paquets issus d'un profil."""
    data = request.get_json(silent=True) or {}
    apt_pkgs     = data.get("apt", [])       # [{name, description}]
    flatpak_apps = data.get("flatpak", [])   # [{app, description}]
    external_pkgs = data.get("external", []) # [{name, description, cmd}]
    remove_pkgs  = data.get("remove", [])    # [{name, description}]

    if not any([apt_pkgs, flatpak_apps, external_pkgs, remove_pkgs]):
        return jsonify({"success": False, "error": "Aucun paquet selectionne"}), 400

    with task_lock:
        if current_task["running"]:
            return jsonify({"success": False, "error": "Tache en cours"}), 409
        total = len(apt_pkgs) + len(flatpak_apps) + len(external_pkgs) + len(remove_pkgs)
        current_task.update(running=True, name=f"Installation personnalisee ({total} paquets)", progress=0)

    def run():
        state = get_state_manager()
        had_errors = False
        done = 0

        try:
            log_info("apt update avant installation...")
            apt_update()

            for pkg in apt_pkgs:
                name, desc = pkg.get("name", ""), pkg.get("description", "")
                if not name:
                    continue
                if check_package_installed(name):
                    log_warn(f"{name} deja installe, ignore.")
                else:
                    log_info(f"APT : {name}")
                    result = apt_install([name])
                    state.record(ACTION_APT_INSTALL, name, result.success,
                                 rollback_cmd=["apt", "remove", "-y", name],
                                 metadata={"description": desc})
                    if not result.success:
                        log_error(f"Echec : {name}")
                        had_errors = True
                done += 1
                update_task_status(f"Installation ({done}/{total})", True, 10 + int((done / total) * 80))

            for fp in flatpak_apps:
                app, desc = fp.get("app", ""), fp.get("description", "")
                if not app:
                    continue
                if check_flatpak_installed(app):
                    log_warn(f"{app} deja installe, ignore.")
                else:
                    log_info(f"Flatpak : {app}")
                    result = flatpak_install(app)
                    state.record(ACTION_FLATPAK_INSTALL, app, result.success,
                                 rollback_cmd=["flatpak", "uninstall", "-y", app],
                                 metadata={"description": desc})
                    if not result.success:
                        log_error(f"Echec : {app}")
                        had_errors = True
                done += 1
                update_task_status(f"Installation ({done}/{total})", True, 10 + int((done / total) * 80))

            for ext in external_pkgs:
                name, desc, cmd = ext.get("name", ""), ext.get("description", ""), ext.get("cmd", "")
                if not name or not cmd:
                    continue
                log_info(f"Externe : {name}")
                result = run_command(["bash", "-c", cmd])
                state.record(ACTION_EXTERNAL_INSTALL, name, result.success,
                             rollback_cmd=[], metadata={"description": desc, "manual_rollback": True})
                if not result.success:
                    log_error(f"Echec : {name}")
                    had_errors = True
                done += 1
                update_task_status(f"Installation ({done}/{total})", True, 10 + int((done / total) * 80))

            for pkg in remove_pkgs:
                name, desc = pkg.get("name", ""), pkg.get("description", "")
                if not name:
                    continue
                if check_package_installed(name):
                    log_info(f"Suppression : {name}")
                    result = apt_remove([name], purge=True)
                    state.record(ACTION_APT_REMOVE, name, result.success,
                                 rollback_cmd=["apt", "install", "-y", name],
                                 metadata={"description": desc})
                    if not result.success:
                        log_error(f"Echec suppression : {name}")
                        had_errors = True
                done += 1
                update_task_status(f"Installation ({done}/{total})", True, 10 + int((done / total) * 80))

            if had_errors:
                update_task_status("Termine avec erreurs", False, 100)
                log_warn("Installation personnalisee terminee avec erreurs.")
            else:
                update_task_status("Installation terminee", False, 100)
                log_success("Installation personnalisee terminee.")
        except Exception as e:
            log_error(f"Erreur installation personnalisee : {e}")
            update_task_status("Erreur", False, 0)

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"success": True, "message": f"Installation de {total} paquet(s) lancee"})


@bp.route('/api/profiles/export', methods=['POST'])
def export_selection():
    data = request.get_json(silent=True) or {}
    return jsonify({"success": True, "export": {"profiles": data.get("profiles", [])}})


@bp.route('/api/profiles/import', methods=['POST'])
def import_selection():
    data = request.get_json(silent=True) or {}
    slugs = data.get("profiles", [])
    valid, invalid = [], []
    for s in slugs:
        (valid if get_profile(s) is not None else invalid).append(s)
    return jsonify({"success": True, "profiles": valid, "invalid": invalid})
