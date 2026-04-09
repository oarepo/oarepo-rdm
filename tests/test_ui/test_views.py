#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for UI redirect views (record_detail, deposit_edit)."""

from __future__ import annotations

from oarepo_rdm.ui.views import _append_query_params
from tests.models import modela

modela_service = modela.proxies.current_service


def test_append_query_params_no_params():
    assert _append_query_params("https://example.com/record/1", {}) == "https://example.com/record/1"


def test_append_query_params_no_existing_query():
    result = _append_query_params("https://example.com/record/1", {"foo": "bar", "baz": "qux"})
    assert result == "https://example.com/record/1?foo=bar&baz=qux"


def test_append_query_params_merges_with_existing_query():
    result = _append_query_params("https://example.com/record/1?existing=2", {"incoming": "1"})
    assert "existing=2" in result
    assert "incoming=1" in result


def test_append_query_params_incoming_overrides_existing():
    result = _append_query_params("https://example.com/record/1?key=old", {"key": "new"})
    assert "key=new" in result
    assert "key=old" not in result


def test_record_detail_redirect(app, search_clear, rdm_records_service, users, client):
    """Test that /records/<pid_value> redirects to the model-specific record detail page."""
    user = users[0]

    # Create and publish a record
    sample_draft = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modela-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    published = rdm_records_service.publish(user.identity, sample_draft["id"])
    pid_value = published["id"]

    modela_service.indexer.refresh()

    # First verify we get a redirect
    response = client.get(f"/records/{pid_value}")
    assert response.status_code == 302
    assert response.location.endswith(f"/modela_ui/record_detail/{pid_value}")

    # Then follow the redirect and verify we get 200
    response = client.get(f"/records/{pid_value}", follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == f"/modela_ui/record_detail/{pid_value}"


def test_record_detail_not_found(client):
    """Test that /records/<pid_value> returns 404 for non-existent record."""
    response = client.get("/records/nonexistent-pid-12345")

    assert response.status_code == 404


def test_deposit_edit_redirect(app, search_clear, rdm_records_service, users, client):
    """Test that /uploads/<pid_value> redirects to the model-specific deposit edit page."""
    user = users[0]

    # Create a draft (don't publish)
    sample_draft = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modela-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    pid_value = sample_draft["id"]
    # First verify we get a redirect
    response = client.get(f"/uploads/{pid_value}")
    assert response.status_code == 302
    assert response.location.endswith(f"/modela_ui/deposit_edit/{pid_value}")

    # Then follow the redirect and verify we get 200
    response = client.get(f"/uploads/{pid_value}", follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == f"/modela_ui/deposit_edit/{pid_value}"


def test_deposit_edit_not_found(client):
    """Test that /uploads/<pid_value> returns 404 for non-existent draft."""
    response = client.get("/uploads/nonexistent-pid-12345")

    assert response.status_code == 404


def test_record_detail_redirect_preserves_query_params(app, search_clear, rdm_records_service, users, client):
    """Test that query params are forwarded in the redirect location."""
    user = users[0]
    sample_draft = rdm_records_service.create(
        user.identity,
        data={"$schema": "local://modela-v1.0.0.json", "files": {"enabled": False}},
    )
    published = rdm_records_service.publish(user.identity, sample_draft["id"])
    pid_value = published["id"]
    modela_service.indexer.refresh()

    response = client.get(f"/records/{pid_value}?embed=1&theme=dark")
    assert response.status_code == 302
    assert "embed=1" in response.location
    assert "theme=dark" in response.location


def test_deposit_edit_redirect_preserves_query_params(app, search_clear, rdm_records_service, users, client):
    """Test that query params are forwarded in the deposit edit redirect location."""
    user = users[0]
    sample_draft = rdm_records_service.create(
        user.identity,
        data={"$schema": "local://modela-v1.0.0.json", "files": {"enabled": False}},
    )
    pid_value = sample_draft["id"]

    response = client.get(f"/uploads/{pid_value}?embed=1")
    assert response.status_code == 302
    assert "embed=1" in response.location
