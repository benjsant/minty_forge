"""Route laptop : detection batterie pour bandeau d'information."""
from flask import Blueprint, jsonify

from utils.laptop_detect import is_laptop

bp = Blueprint("laptop", __name__)


@bp.route("/api/laptop/detect")
def detect():
    detected, battery = is_laptop()
    return jsonify(is_laptop=detected, battery=battery)
