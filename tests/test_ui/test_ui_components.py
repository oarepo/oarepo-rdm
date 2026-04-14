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

import json

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


def test_deposit_form_defaults_publication_date(app, modelb_ui_resource):
    """Test that APP_RDM_DEPOSIT_FORM_DEFAULTS sets publication_date to today."""
    empty_data = {}
    with app.test_request_context():
        modelb_ui_resource.run_components("empty_record", empty_data=empty_data)

    expected = app.config["APP_RDM_DEPOSIT_FORM_DEFAULTS"]["publication_date"]()
    assert empty_data.get("metadata", {}).get("publication_date") == expected


def test_files_enabled_component_sets_true(app, modelb_ui_resource, monkeypatch):
    """Test that FilesEnabledComponent sets files.enabled=True from config."""
    files_enabled = True
    monkeypatch.setitem(app.config, "RDM_DEFAULT_FILES_ENABLED", files_enabled)

    empty_data = {}
    with app.test_request_context():
        modelb_ui_resource.run_components("empty_record", empty_data=empty_data)

    assert empty_data.get("files", {}).get("enabled") is True


def test_files_enabled_component_sets_false(app, modelb_ui_resource, monkeypatch):
    """Test that FilesEnabledComponent sets files.enabled=False from config."""
    files_enabled = False
    monkeypatch.setitem(app.config, "RDM_DEFAULT_FILES_ENABLED", files_enabled)

    empty_data = {}
    with app.test_request_context():
        modelb_ui_resource.run_components("empty_record", empty_data=empty_data)

    assert empty_data.get("files", {}).get("enabled") is False


def _get_hidden_input(response, input_name) -> dict:
    """Extract a hidden input's JSON value from the HTML response."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.data, "html.parser")
    tag = soup.find("input", {"name": input_name})
    assert tag, f"hidden input '{input_name}' not found in response"
    return json.loads(tag["value"])


def test_create_page_contains_publication_date(
    app, db, users, vocab_fixtures, logged_client, search_clear, extra_entry_points
):
    """Test that the create page contains publication_date from APP_RDM_DEPOSIT_FORM_DEFAULTS."""
    user = users[0]
    client = logged_client(user)

    response = client.get("/modelb/uploads/new")
    assert response.status_code == 200

    record = _get_hidden_input(response, "deposits-record")
    expected = app.config["APP_RDM_DEPOSIT_FORM_DEFAULTS"]["publication_date"]()

    assert record.get("metadata", {}).get("publication_date") == expected


def test_create_page_contains_files_enabled(
    app, db, users, vocab_fixtures, logged_client, search_clear, extra_entry_points
):
    """Test that the create page contains files.enabled from RDM_DEFAULT_FILES_ENABLED."""
    user = users[0]
    client = logged_client(user)

    response = client.get("/modelb/uploads/new")
    assert response.status_code == 200

    record = _get_hidden_input(response, "deposits-record")
    assert record.get("files", {}).get("enabled") is app.config["RDM_DEFAULT_FILES_ENABLED"]


def test_create_page_contains_pids_with_doi(
    app, db, users, vocab_fixtures, logged_client, search_clear, extra_entry_points, monkeypatch
):
    """Test that the create page contains pids with doi when DOI providers are configured."""
    from invenio_i18n import lazy_gettext as _
    from invenio_rdm_records.services.pids import providers

    monkeypatch.setitem(app.config, "DATACITE_ENABLED", True)  # NOQA: FBT003
    monkeypatch.setitem(
        app.config,
        "RDM_PERSISTENT_IDENTIFIER_PROVIDERS",
        [
            providers.DataCitePIDProvider(
                "datacite",
                client=providers.DataCiteClient("datacite", config_prefix="DATACITE"),
                label=_("DOI"),
            ),
            providers.ExternalPIDProvider(
                "external",
                "doi",
                validators=[providers.BlockedPrefixes(config_names=["DATACITE_PREFIX"])],
                label=_("DOI"),
            ),
            providers.OAIPIDProvider(
                "oai",
                label=_("OAI ID"),
            ),
        ],
    )

    import idutils

    monkeypatch.setitem(
        app.config,
        "RDM_PERSISTENT_IDENTIFIERS",
        {
            "doi": {
                "providers": ["datacite", "external"],
                "required": True,
                "label": _("DOI"),
                "validator": idutils.is_doi,
                "normalizer": idutils.normalize_doi,
                "is_enabled": providers.DataCitePIDProvider.is_enabled,
                "ui": {"default_selected": "yes"},
            },
            "oai": {
                "providers": ["oai"],
                "required": True,
                "label": _("OAI"),
                "is_enabled": providers.OAIPIDProvider.is_enabled,
            },
        },
    )

    user = users[0]
    client = logged_client(user)

    response = client.get("/modelb/uploads/new")
    assert response.status_code == 200

    record = _get_hidden_input(response, "deposits-record")
    assert record["pids"] == {"doi": {"provider": "external", "identifier": ""}}


def test_create_page_contains_empty_pids_when_not_default_selected(
    app, db, users, vocab_fixtures, logged_client, search_clear, extra_entry_points, monkeypatch
):
    """Test that pids is empty when doi default_selected is not 'yes'."""
    import idutils
    from invenio_i18n import lazy_gettext as _
    from invenio_rdm_records.services.pids import providers

    monkeypatch.setitem(app.config, "DATACITE_ENABLED", True)  # NOQA: FBT003
    monkeypatch.setitem(
        app.config,
        "RDM_PERSISTENT_IDENTIFIER_PROVIDERS",
        [
            providers.DataCitePIDProvider(
                "datacite",
                client=providers.DataCiteClient("datacite", config_prefix="DATACITE"),
                label=_("DOI"),
            ),
            providers.ExternalPIDProvider(
                "external",
                "doi",
                validators=[providers.BlockedPrefixes(config_names=["DATACITE_PREFIX"])],
                label=_("DOI"),
            ),
            providers.OAIPIDProvider(
                "oai",
                label=_("OAI ID"),
            ),
        ],
    )
    monkeypatch.setitem(
        app.config,
        "RDM_PERSISTENT_IDENTIFIERS",
        {
            "doi": {
                "providers": ["datacite", "external"],
                "required": True,
                "label": _("DOI"),
                "validator": idutils.is_doi,
                "normalizer": idutils.normalize_doi,
                "is_enabled": providers.DataCitePIDProvider.is_enabled,
                "ui": {"default_selected": "no"},
            },
            "oai": {
                "providers": ["oai"],
                "required": True,
                "label": _("OAI"),
                "is_enabled": providers.OAIPIDProvider.is_enabled,
            },
        },
    )

    user = users[0]
    client = logged_client(user)

    response = client.get("/modelb/uploads/new")
    assert response.status_code == 200

    record = _get_hidden_input(response, "deposits-record")
    assert record["pids"] == {}


def test_create_page_contains_doi_required(
    app, db, users, vocab_fixtures, logged_client, search_clear, extra_entry_points, monkeypatch
):
    """Test that the create page contains is_doi_required in deposits-config."""
    import idutils
    from invenio_i18n import lazy_gettext as _
    from invenio_rdm_records.services.pids import providers

    monkeypatch.setitem(
        app.config,
        "RDM_PERSISTENT_IDENTIFIERS",
        {
            "doi": {
                "providers": ["datacite", "external"],
                "required": True,
                "label": _("DOI"),
                "validator": idutils.is_doi,
                "normalizer": idutils.normalize_doi,
                "is_enabled": providers.DataCitePIDProvider.is_enabled,
                "ui": {"default_selected": "yes"},
            },
            "oai": {
                "providers": ["oai"],
                "required": True,
                "label": _("OAI"),
                "is_enabled": providers.OAIPIDProvider.is_enabled,
            },
        },
    )

    user = users[0]
    client = logged_client(user)

    response = client.get("/modelb/uploads/new")
    assert response.status_code == 200

    config = _get_hidden_input(response, "deposits-config")
    assert config["is_doi_required"] is True


def test_edit_page_contains_doi_required(
    app, db, users, vocab_fixtures, logged_client, search_clear, extra_entry_points, monkeypatch
):
    """Test that the edit page contains is_doi_required in deposits-config."""
    import idutils
    from invenio_i18n import lazy_gettext as _
    from invenio_rdm_records.services.pids import providers

    from tests.models import modelb

    monkeypatch.setitem(
        app.config,
        "RDM_PERSISTENT_IDENTIFIERS",
        {
            "doi": {
                "providers": ["datacite", "external"],
                "required": True,
                "label": _("DOI"),
                "validator": idutils.is_doi,
                "normalizer": idutils.normalize_doi,
                "is_enabled": providers.DataCitePIDProvider.is_enabled,
                "ui": {"default_selected": "yes"},
            },
            "oai": {
                "providers": ["oai"],
                "required": True,
                "label": _("OAI"),
                "is_enabled": providers.OAIPIDProvider.is_enabled,
            },
        },
    )

    user = users[0]
    modelb_service = modelb.proxies.current_service
    draft = modelb_service.create(
        user.identity,
        {
            "metadata": {"title": "Test B", "bdescription": "desc b"},
            "files": {"enabled": False},
        },
    )

    client = logged_client(user)
    response = client.get(f"/modelb/uploads/{draft['id']}")
    assert response.status_code == 200

    config = _get_hidden_input(response, "deposits-config")
    assert config["is_doi_required"] is True


def test_inject_parent_doi_on_draft_preview(
    app, db, users, search_clear, extra_entry_points, monkeypatch, modelb_ui_resource
):
    """Test that InjectParentDoiComponent injects parent DOI on draft preview."""
    import idutils
    from invenio_i18n import lazy_gettext as _
    from invenio_rdm_records.services.pids import providers

    from tests.models import modelb

    monkeypatch.setitem(app.config, "DATACITE_ENABLED", True)  # NOQA: FBT003
    monkeypatch.setitem(app.config, "DATACITE_PREFIX", "10.5072")
    monkeypatch.setitem(
        app.config,
        "RDM_PERSISTENT_IDENTIFIER_PROVIDERS",
        [
            providers.DataCitePIDProvider(
                "datacite",
                client=providers.DataCiteClient("datacite", config_prefix="DATACITE"),
                label=_("DOI"),
            ),
            providers.ExternalPIDProvider(
                "external",
                "doi",
                validators=[providers.BlockedPrefixes(config_names=["DATACITE_PREFIX"])],
                label=_("DOI"),
            ),
            providers.OAIPIDProvider(
                "oai",
                label=_("OAI ID"),
            ),
        ],
    )
    monkeypatch.setitem(
        app.config,
        "RDM_PERSISTENT_IDENTIFIERS",
        {
            "doi": {
                "providers": ["datacite", "external"],
                "required": True,
                "label": _("DOI"),
                "validator": idutils.is_doi,
                "normalizer": idutils.normalize_doi,
                "is_enabled": providers.DataCitePIDProvider.is_enabled,
                "ui": {"default_selected": "yes"},
            },
            "oai": {
                "providers": ["oai"],
                "required": True,
                "label": _("OAI"),
                "is_enabled": providers.OAIPIDProvider.is_enabled,
            },
        },
    )
    monkeypatch.setitem(
        app.config,
        "RDM_PARENT_PERSISTENT_IDENTIFIERS",
        {
            "doi": {
                "providers": ["datacite"],
                "required": True,
                "label": _("DOI"),
                "is_enabled": providers.DataCitePIDProvider.is_enabled,
            },
        },
    )

    user = users[0]
    modelb_service = modelb.proxies.current_service
    draft = modelb_service.create(
        user.identity,
        {
            "metadata": {"title": "Test B", "bdescription": "desc b"},
            "files": {"enabled": False},
        },
    )
    api_record = modelb_service.read_draft(user.identity, draft["id"])

    record_ui = {}
    render_kwargs = {"record_ui": record_ui, "is_preview": True, "is_draft": True}
    with app.test_request_context():
        modelb_ui_resource.run_components(
            "before_ui_detail",
            api_record=api_record,
            record={},
            identity=user.identity,
            ui_links={},
            extra_context={},
            render_kwargs=render_kwargs,
        )

    assert "new_draft_parent_doi" in record_ui.get("ui", {})


def test_inject_parent_doi_skipped_when_not_preview(
    app, db, users, search_clear, extra_entry_points, modelb_ui_resource
):
    """Test that InjectParentDoiComponent does nothing when is_preview=False."""
    from tests.models import modelb

    user = users[0]
    modelb_service = modelb.proxies.current_service
    draft = modelb_service.create(
        user.identity,
        {
            "metadata": {"title": "Test B", "bdescription": "desc b"},
            "files": {"enabled": False},
        },
    )
    api_record = modelb_service.read_draft(user.identity, draft["id"])

    record_ui = {}
    render_kwargs = {"record_ui": record_ui, "is_preview": False, "is_draft": True}
    with app.test_request_context():
        modelb_ui_resource.run_components(
            "before_ui_detail",
            api_record=api_record,
            record={},
            identity=user.identity,
            ui_links={},
            extra_context={},
            render_kwargs=render_kwargs,
        )

    assert "new_draft_parent_doi" not in record_ui.get("ui", {})


def test_inject_parent_doi_skipped_when_datacite_disabled(
    app, db, users, search_clear, extra_entry_points, monkeypatch, modelb_ui_resource
):
    """Test that InjectParentDoiComponent does nothing when DATACITE_ENABLED=False."""
    from tests.models import modelb

    monkeypatch.setitem(app.config, "DATACITE_ENABLED", False)  # noqa: FBT003

    user = users[0]
    modelb_service = modelb.proxies.current_service
    draft = modelb_service.create(
        user.identity,
        {
            "metadata": {"title": "Test B", "bdescription": "desc b"},
            "files": {"enabled": False},
        },
    )
    api_record = modelb_service.read_draft(user.identity, draft["id"])

    record_ui = {}
    render_kwargs = {"record_ui": record_ui, "is_preview": True, "is_draft": True}
    with app.test_request_context():
        modelb_ui_resource.run_components(
            "before_ui_detail",
            api_record=api_record,
            record={},
            identity=user.identity,
            ui_links={},
            extra_context={},
            render_kwargs=render_kwargs,
        )

    assert "new_draft_parent_doi" not in record_ui.get("ui", {})


def test_inject_parent_doi_skipped_when_no_datacite_provider(
    app, db, users, search_clear, extra_entry_points, monkeypatch, modelb_ui_resource
):
    """Test that InjectParentDoiComponent does nothing when no datacite parent provider."""
    from invenio_rdm_records.services.pids import providers

    from tests.models import modelb

    monkeypatch.setitem(app.config, "DATACITE_ENABLED", True)  # noqa: FBT003
    monkeypatch.setitem(
        app.config,
        "RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS",
        [
            providers.OAIPIDProvider(
                "oai",
                label="OAI ID",
            ),
        ],
    )
    monkeypatch.setitem(
        app.config,
        "RDM_PARENT_PERSISTENT_IDENTIFIERS",
        {
            "oai": {
                "providers": ["oai"],
                "required": True,
                "label": "OAI",
                "is_enabled": providers.OAIPIDProvider.is_enabled,
            },
        },
    )

    user = users[0]
    modelb_service = modelb.proxies.current_service
    draft = modelb_service.create(
        user.identity,
        {
            "metadata": {"title": "Test B", "bdescription": "desc b"},
            "files": {"enabled": False},
        },
    )
    api_record = modelb_service.read_draft(user.identity, draft["id"])

    record_ui = {}
    render_kwargs = {"record_ui": record_ui, "is_preview": True, "is_draft": True}
    with app.test_request_context():
        modelb_ui_resource.run_components(
            "before_ui_detail",
            api_record=api_record,
            record={},
            identity=user.identity,
            ui_links={},
            extra_context={},
            render_kwargs=render_kwargs,
        )

    assert "new_draft_parent_doi" not in record_ui.get("ui", {})


def test_inject_parent_doi_skipped_when_not_required_and_no_reserved_doi(
    app, db, users, search_clear, extra_entry_points, monkeypatch, modelb_ui_resource
):
    """Test that parent DOI is not injected when doi is not required and no reserved doi."""
    import idutils
    from invenio_i18n import lazy_gettext as _
    from invenio_rdm_records.services.pids import providers

    from tests.models import modelb

    monkeypatch.setitem(app.config, "DATACITE_ENABLED", True)  # noqa: FBT003
    monkeypatch.setitem(app.config, "DATACITE_PREFIX", "10.5072")
    monkeypatch.setitem(
        app.config,
        "RDM_PERSISTENT_IDENTIFIER_PROVIDERS",
        [
            providers.DataCitePIDProvider(
                "datacite",
                client=providers.DataCiteClient("datacite", config_prefix="DATACITE"),
                label=_("DOI"),
            ),
            providers.ExternalPIDProvider(
                "external",
                "doi",
                validators=[providers.BlockedPrefixes(config_names=["DATACITE_PREFIX"])],
                label=_("DOI"),
            ),
            providers.OAIPIDProvider(
                "oai",
                label=_("OAI ID"),
            ),
        ],
    )
    monkeypatch.setitem(
        app.config,
        "RDM_PERSISTENT_IDENTIFIERS",
        {
            "doi": {
                "providers": ["datacite", "external"],
                "required": True,
                "label": _("DOI"),
                "validator": idutils.is_doi,
                "normalizer": idutils.normalize_doi,
                "is_enabled": providers.DataCitePIDProvider.is_enabled,
                "ui": {"default_selected": "yes"},
            },
            "oai": {
                "providers": ["oai"],
                "required": True,
                "label": _("OAI"),
                "is_enabled": providers.OAIPIDProvider.is_enabled,
            },
        },
    )
    monkeypatch.setitem(
        app.config,
        "RDM_PARENT_PERSISTENT_IDENTIFIERS",
        {
            "doi": {
                "providers": ["datacite"],
                "required": False,
                "label": _("DOI"),
                "is_enabled": providers.DataCitePIDProvider.is_enabled,
            },
        },
    )

    user = users[0]
    modelb_service = modelb.proxies.current_service
    draft = modelb_service.create(
        user.identity,
        {
            "metadata": {"title": "Test B", "bdescription": "desc b"},
            "files": {"enabled": False},
        },
    )
    api_record = modelb_service.read_draft(user.identity, draft["id"])

    record_ui = {}
    render_kwargs = {"record_ui": record_ui, "is_preview": True, "is_draft": True}
    with app.test_request_context():
        modelb_ui_resource.run_components(
            "before_ui_detail",
            api_record=api_record,
            record={},
            identity=user.identity,
            ui_links={},
            extra_context={},
            render_kwargs=render_kwargs,
        )

    assert "new_draft_parent_doi" not in record_ui.get("ui", {})
