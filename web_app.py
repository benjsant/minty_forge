#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MintyForge - Interface web Flask."""

from flask import Flask, jsonify, render_template, request

from routes import legacy, profiles, state_routes, system, themes, greeter, laptop
from routes.shared import log_info, log_warn

app = Flask(__name__,
            template_folder='web/templates',
            static_folder='web/static')
app.json.sort_keys = False

# Origines autorisees pour les requetes mutantes (Flask ecoute sur 127.0.0.1:5000).
_ALLOWED_ORIGINS = (
    "http://localhost:5000",
    "http://127.0.0.1:5000",
)
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@app.before_request
def _origin_guard():
    """Protege les routes mutantes contre les requetes inter-origine (CSRF basique).

    Le serveur tourne en local : on accepte uniquement les requetes dont l'Origin
    ou le Referer pointe vers http://localhost:5000 / http://127.0.0.1:5000.
    """
    if request.method not in _MUTATING_METHODS:
        return None
    origin = request.headers.get("Origin", "")
    if origin and origin in _ALLOWED_ORIGINS:
        return None
    referer = request.headers.get("Referer", "")
    if referer and any(referer.startswith(o + "/") or referer == o for o in _ALLOWED_ORIGINS):
        return None
    log_warn(f"Requete {request.method} {request.path} bloquee (Origin={origin!r}, Referer={referer!r})")
    return jsonify({"success": False, "error": "Origine non autorisee"}), 403


# Politique de securite restrictive — defense en profondeur contre XSS et
# clickjacking. 'unsafe-inline' reste necessaire tant que index.html contient
# des handlers onclick="" et des attributs style="" inline.
_CSP_POLICY = (
    "default-src 'self'; "
    "img-src 'self' data:; "
    "style-src 'self' 'unsafe-inline'; "
    "script-src 'self' 'unsafe-inline'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


@app.after_request
def _security_headers(response):
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Content-Security-Policy", _CSP_POLICY)
    return response


app.register_blueprint(legacy.bp)
app.register_blueprint(profiles.bp)
app.register_blueprint(state_routes.bp)
app.register_blueprint(system.bp)
app.register_blueprint(themes.bp)
app.register_blueprint(greeter.bp)
app.register_blueprint(laptop.bp)


@app.route('/')
def index():
    return render_template('index.html')


def main():
    log_info("MintyForge demarre sur http://localhost:5000")
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)


if __name__ == '__main__':
    main()
