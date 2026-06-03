#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke tests Flask : verifient que les principales routes repondent
sans 500 et que la garde Origin/Referer bloque bien les requetes
inter-origine. N'effectue aucune action systeme (pas d'install reelle)."""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from web_app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ─── Pages et routes GET ──────────────────────────────────────────────

def test_index_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"MintyForge" in r.data


def test_status_responds(client):
    r = client.get("/api/status")
    assert r.status_code == 200
    j = r.get_json()
    assert "checks" in j
    assert "packages" in j
    assert "task" in j


def test_profiles_list(client):
    r = client.get("/api/profiles")
    assert r.status_code == 200
    j = r.get_json()
    assert j["success"] is True
    assert "profiles" in j


def test_profile_detail_unknown(client):
    r = client.get("/api/profiles/does-not-exist")
    assert r.status_code == 404


def test_state_history(client):
    r = client.get("/api/state")
    assert r.status_code == 200
    j = r.get_json()
    assert j["success"] is True
    assert "history" in j


def test_laptop_detect(client):
    r = client.get("/api/laptop/detect")
    assert r.status_code == 200
    j = r.get_json()
    assert "is_laptop" in j


def test_greeter_status(client):
    r = client.get("/api/greeter/status")
    # Peut etre 500 si crudini absent — on accepte 200 ou 500 mais pas crash
    assert r.status_code in (200, 500)


def test_themes_catalog(client):
    r = client.get("/api/themes/catalog")
    assert r.status_code == 200
    j = r.get_json()
    assert "catalog" in j or "success" in j


# ─── Garde Origin / Referer sur les routes mutantes ──────────────────

def test_post_blocked_without_origin(client):
    """Un POST sans Origin ni Referer doit etre refuse (403)."""
    r = client.post("/api/profiles/install",
                    json={"profiles": ["base"]},
                    headers={})
    assert r.status_code == 403


def test_post_blocked_with_evil_origin(client):
    """Un POST avec Origin etranger doit etre refuse (403)."""
    r = client.post("/api/profiles/install",
                    json={"profiles": ["base"]},
                    headers={"Origin": "http://evil.example.com"})
    assert r.status_code == 403


def test_post_allowed_with_localhost_origin(client):
    """Un POST avec Origin localhost passe la garde (peut renvoyer 400/409/etc
    selon la logique metier, mais surtout pas 403)."""
    r = client.post("/api/profiles/install",
                    json={"profiles": []},
                    headers={"Origin": "http://localhost:5000"})
    assert r.status_code != 403


def test_post_install_custom_rejects_unknown_slug(client):
    """install-custom refuse un slug inconnu, meme avec Origin valide."""
    r = client.post("/api/profiles/install-custom",
                    json={"slug": "does-not-exist", "apt": ["foo"]},
                    headers={"Origin": "http://localhost:5000"})
    assert r.status_code == 404


def test_post_install_custom_requires_slug(client):
    r = client.post("/api/profiles/install-custom",
                    json={"apt": ["foo"]},
                    headers={"Origin": "http://localhost:5000"})
    assert r.status_code == 400


# ─── Reload caches profils ───────────────────────────────────────────

def test_profiles_reload(client):
    r = client.post("/api/profiles/reload",
                    headers={"Origin": "http://localhost:5000"})
    assert r.status_code == 200
    assert r.get_json()["success"] is True


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
