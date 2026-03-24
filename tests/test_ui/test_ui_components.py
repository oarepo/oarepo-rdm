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

from flask import g

from oarepo_rdm.ui.config import RDMRecordsUIResourceConfig


def test_form_config_contains_communities_memberships_and_vocabularies(
    app, db, users, vocab_fixtures, modela_ui_resource_config, modela_ui_resource
):
    """Test that form config includes data from RDM components."""
    user = users[0]
    fc = modela_ui_resource_config.form_config()

    with app.test_request_context():
        g.identity = user.identity

        modela_ui_resource.run_components(
            "form_config",
            form_config=fc,
            layout="",
            resource=modela_ui_resource,
            api_record=None,
            record={},
            data={},
            identity=user.identity,
            extra_context={},
            ui_links={},
        )

    # CommunitiesMembershipsComponent should add user_communities_memberships
    assert "user_communities_memberships" in fc

    # RDMVocabularyOptionsComponent should add vocabularies
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


def test_modelb_uses_rdm_records_ui_resource_config(modelb_ui_resource_config):
    """Test that ModelbUIResourceConfig inherits from RDMRecordsUIResourceConfig."""
    assert isinstance(modelb_ui_resource_config, RDMRecordsUIResourceConfig)


def test_modelb_has_expected_components(modelb_ui_resource_config, modelb_ui_resource):
    """Test that modelb has the expected components from RDMRecordsUIResourceConfig."""
    # ModelbUIResourceConfig should have components from parent class
    assert hasattr(modelb_ui_resource_config, "components")
    assert len(list(modelb_ui_resource.components)) == len(list(RDMRecordsUIResourceConfig().components))
