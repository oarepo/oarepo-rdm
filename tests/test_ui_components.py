#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for UI components."""

from __future__ import annotations

from typing import Any

from flask import g


def _run_form_config_components(
    app, user, modela_ui_resource_config, modela_ui_resource, record=None
) -> dict[str, Any]:
    """Run form_config components and return the form config."""
    fc = modela_ui_resource_config.form_config()

    with app.test_request_context():
        g.identity = user.identity

        modela_ui_resource.run_components(
            "form_config",
            form_config=fc,
            resource=modela_ui_resource,
            api_record=None,
            record=record,
            data={},
            identity=user.identity,
            extra_context={},
            ui_links={},
        )

    return fc


def test_communities_memberships_component(
    app, db, users, vocab_fixtures, modela_ui_resource_config, modela_ui_resource
):
    """Test that CommunitiesMembershipsComponent adds user_communities_memberships."""
    user = users[0]
    fc = _run_form_config_components(app, user, modela_ui_resource_config, modela_ui_resource)

    assert "user_communities_memberships" in fc


def test_vocabularies_component(app, db, users, vocab_fixtures, modela_ui_resource_config, modela_ui_resource):
    """Test that RDMVocabularyOptionsComponent adds vocabularies to form config."""
    user = users[0]
    fc = _run_form_config_components(app, user, modela_ui_resource_config, modela_ui_resource)

    assert "vocabularies" in fc
    vocabularies = fc["vocabularies"]

    # Check resource_type from vocab_fixtures (uses "id" key, not "value")
    assert "resource_type" in vocabularies
    assert any(rt["id"] == "image-photo" for rt in vocabularies["resource_type"])

    # Check other vocabulary types are present
    assert "titles" in vocabularies
    assert "type" in vocabularies["titles"]

    assert "creators" in vocabularies
    assert "role" in vocabularies["creators"]

    assert "contributors" in vocabularies
    assert "role" in vocabularies["contributors"]

    assert "descriptions" in vocabularies
    assert "type" in vocabularies["descriptions"]

    assert "dates" in vocabularies
    assert "type" in vocabularies["dates"]


def test_pids_config_component(app, db, users, modela_ui_resource_config, modela_ui_resource):
    """Test that RDMPIDsConfigComponent adds pids configuration to form config."""
    user = users[0]
    fc = _run_form_config_components(app, user, modela_ui_resource_config, modela_ui_resource)

    assert "pids" in fc
    pids = fc["pids"]

    # pids should be a list of PID provider configurations
    assert isinstance(pids, list)


def test_pids_config_component_with_doi_required(
    app, db, users, modela_ui_resource_config, modela_ui_resource, monkeypatch
):
    """Test PIDs config when DOI is configured as required."""
    user = users[0]

    monkeypatch.setitem(
        app.config,
        "RDM_PERSISTENT_IDENTIFIERS",
        {
            "doi": {
                "providers": ["datacite", "external"],
                "required": True,
                "label": "DOI",
                "is_enabled": lambda _: True,
                "ui": {"default_selected": "yes"},
            },
        },
    )

    fc = _run_form_config_components(app, user, modela_ui_resource_config, modela_ui_resource)

    assert "pids" in fc
    pids = fc["pids"]
    assert isinstance(pids, list)
    assert len(pids) == 1

    doi_config = pids[0]
    assert doi_config["scheme"] == "doi"
    assert doi_config["pid_label"] == "DOI"
    assert doi_config["can_be_managed"] is True
    assert doi_config["can_be_unmanaged"] is True
    assert doi_config["default_selected"] == "yes"


def test_pids_config_component_with_doi_not_required(
    app, db, users, modela_ui_resource_config, modela_ui_resource, monkeypatch
):
    """Test PIDs config when DOI is configured as not required."""
    user = users[0]

    monkeypatch.setitem(
        app.config,
        "RDM_PERSISTENT_IDENTIFIERS",
        {
            "doi": {
                "providers": ["datacite", "external"],
                "required": False,
                "label": "DOI",
                "is_enabled": lambda _: True,
                "ui": {"default_selected": "not_needed"},
            },
        },
    )

    fc = _run_form_config_components(app, user, modela_ui_resource_config, modela_ui_resource)

    assert "pids" in fc
    pids = fc["pids"]
    assert isinstance(pids, list)
    assert len(pids) == 1

    doi_config = pids[0]
    assert doi_config["scheme"] == "doi"
    assert doi_config["default_selected"] == "not_needed"


def test_pids_config_component_empty_when_no_doi(
    app, db, users, modela_ui_resource_config, modela_ui_resource, monkeypatch
):
    """Test PIDs config returns empty list when no DOI is configured."""
    user = users[0]

    monkeypatch.setitem(app.config, "RDM_PERSISTENT_IDENTIFIERS", {})

    fc = _run_form_config_components(app, user, modela_ui_resource_config, modela_ui_resource)

    assert "pids" in fc
    pids = fc["pids"]
    assert isinstance(pids, list)
    assert len(pids) == 0
