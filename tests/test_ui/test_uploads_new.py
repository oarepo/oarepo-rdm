#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for the generic /uploads/new (uploads_new) route in oarepo_rdm.ui.views."""

from __future__ import annotations


def test_uploads_new_requires_login(app, client, extra_entry_points):
    """Test that /uploads/new requires authentication."""
    with client.get("/uploads/new") as resp:
        # Should redirect to login page

        assert resp.status_code == 302
        assert "login" in resp.location.lower()


def test_uploads_new_single_model_redirect(app, logged_client, users, extra_entry_points, monkeypatch):
    """Test that /uploads/new redirects to the model uploads_new when only one model is registered."""
    monkeypatch.setitem(
        app.config,
        "OAREPO_MODELS",
        {"modelb": app.config["OAREPO_MODELS"]["modelb"]},
    )
    client = logged_client(users[0])
    with client.get("/uploads/new") as resp:
        assert resp.status_code == 302
        assert resp.location.endswith("/modelb/uploads/new")


def test_uploads_new_single_model_with_community(app, logged_client, users, extra_entry_points, monkeypatch):
    """Test that /uploads/new preserves the community query parameter when redirecting."""
    monkeypatch.setitem(
        app.config,
        "OAREPO_MODELS",
        {"modelb": app.config["OAREPO_MODELS"]["modelb"]},
    )
    client = logged_client(users[0])
    with client.get("/uploads/new?community=test-community") as resp:
        assert resp.status_code == 302
        assert "/modelb/uploads/new" in resp.location
        assert "community=test-community" in resp.location


def test_uploads_new_multiple_models_renders_selection(app, logged_client, users, extra_entry_points, monkeypatch):
    """Test that /uploads/new renders the model selection page when multiple models are registered."""
    monkeypatch.setitem(
        app.config,
        "OAREPO_MODELS",
        {
            "modelb": app.config["OAREPO_MODELS"]["modelb"],
            "modelc": app.config["OAREPO_MODELS"]["modelc"],
        },
    )
    client = logged_client(users[0])
    with client.get("/uploads/new") as resp:
        assert resp.status_code == 200
        body = resp.data.decode()
        assert "/modelb/uploads/new" in body
        assert "/modelc/uploads/new" in body


def test_uploads_new_multiple_models_with_community(app, logged_client, users, extra_entry_points, monkeypatch):
    """Test that /uploads/new propagates the community query parameter into each model link."""
    monkeypatch.setitem(
        app.config,
        "OAREPO_MODELS",
        {
            "modelb": app.config["OAREPO_MODELS"]["modelb"],
            "modelc": app.config["OAREPO_MODELS"]["modelc"],
        },
    )
    client = logged_client(users[0])
    with client.get("/uploads/new?community=test-community") as resp:
        assert resp.status_code == 200
        body = resp.data.decode()
        assert "/modelb/uploads/new" in body
        assert "/modelc/uploads/new" in body
        assert body.count("community=test-community") >= 2


def test_uploads_new_single_model_without_ui_blueprint_name(app, logged_client, users, extra_entry_points, monkeypatch):
    """Test that /uploads/new returns 404 when the only model has no ui_blueprint_name."""
    modelb = app.config["OAREPO_MODELS"]["modelb"]
    monkeypatch.setattr(modelb, "_ui_blueprint_name", None)
    monkeypatch.setitem(
        app.config,
        "OAREPO_MODELS",
        {"modelb": modelb},
    )
    client = logged_client(users[0])
    with client.get("/uploads/new") as resp:
        assert resp.status_code == 404
