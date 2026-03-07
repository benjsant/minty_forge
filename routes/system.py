"""Routes /api/system - gestion systeme directe (pare-feu, etc.)."""
import subprocess
from flask import Blueprint, jsonify

bp = Blueprint("system", __name__)


def _ufw(args, timeout=10):
    try:
        r = subprocess.run(["sudo", "-n", "ufw"] + args,
                           capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return False, "", str(e)


@bp.route('/api/system/firewall')
def firewall_status():
    ok, out, err = _ufw(["status", "verbose"])
    if not ok:
        return jsonify({"success": False, "error": err or "sudo requis ou ufw absent"})
    return jsonify({
        "success": True,
        "enabled": "Status: active" in out,
        "output": out,
    })


@bp.route('/api/system/firewall/enable', methods=['POST'])
def firewall_enable():
    ok, out, err = _ufw(["--force", "enable"])
    if not ok:
        return jsonify({"success": False, "error": err or "Echec activation"}), 500
    return jsonify({"success": True, "message": "Pare-feu active"})


@bp.route('/api/system/firewall/disable', methods=['POST'])
def firewall_disable():
    ok, out, err = _ufw(["disable"])
    if not ok:
        return jsonify({"success": False, "error": err or "Echec desactivation"}), 500
    return jsonify({"success": True, "message": "Pare-feu desactive"})
