#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for oarepo_rdm.ext._populate_facet_configs.

Exercises the real Flask app — three test models (modela/b/c) are registered
in tests/models.py, finalize_app runs at app boot, and we assert the resulting
config keys plus a round-trip filter through rdm_records_service.
"""

from __future__ import annotations

from invenio_records_resources.services.records.facets import TermsFacet

from .models import modela, modelb, modelc

modela_service = modela.proxies.current_service
modelb_service = modelb.proxies.current_service
modelc_service = modelc.proxies.current_service


def test_rdm_facets_populated_from_models(app):
    """RDM_FACETS is the FE-shaped union of every model's facets across views."""
    rdm_facets = app.config["RDM_FACETS"]
    assert isinstance(rdm_facets, dict)
    assert rdm_facets, "RDM_FACETS must be populated"

    # modela explicitly registers a model-specific facet in tests/models.py.
    assert "metadata_adescription" in rdm_facets

    # Each entry must use the FE wrapper shape expected by invenio_search_ui.
    for name, entry in rdm_facets.items():
        assert "facet" in entry, f"{name} missing 'facet' key"
        assert "ui" in entry, f"{name} missing 'ui' key"
        assert isinstance(entry["facet"], TermsFacet)
        assert entry["ui"].get("field") == name


def test_per_view_facets_lists_match_merged_options(app):
    """Each FE search config exposes the merged facet names for its view."""
    ext = app.extensions["oarepo-rdm"]
    published = list(ext.search_options.facets.keys())
    drafts = list(ext.draft_search_options.facets.keys())
    versions = list(ext.versions_search_options.facets.keys())

    assert app.config["RDM_SEARCH"]["facets"] == published
    assert app.config["RDM_SEARCH_DRAFTS"]["facets"] == drafts
    assert app.config["RDM_SEARCH_VERSIONING"]["facets"] == versions
    # Community records share the published-search backend.
    assert app.config["COMMUNITIES_RECORDS_SEARCH"]["facets"] == published


def test_per_view_lists_are_subset_of_pool(app):
    """Every per-view selection must exist in the RDM_FACETS pool."""
    pool = set(app.config["RDM_FACETS"].keys())
    for cfg_key in (
        "RDM_SEARCH",
        "RDM_SEARCH_DRAFTS",
        "RDM_SEARCH_VERSIONING",
        "COMMUNITIES_RECORDS_SEARCH",
    ):
        missing = set(app.config[cfg_key]["facets"]) - pool
        assert not missing, f"{cfg_key} lists facets absent from RDM_FACETS: {missing}"


def test_model_specific_facet_filters_through_global_service(
    db, rdm_records_service, identity_simple, vocab_fixtures, required_rdm_metadata, search_clear
):
    """Selecting a per-model facet via the multiplexed service narrows the hits."""
    record_a1 = modela_service.create(
        identity_simple,
        {"metadata": {"title": "blah", "adescription": "1"}, "files": {"enabled": False}},
    )
    record_a2 = modela_service.create(
        identity_simple,
        {"metadata": {"title": "aaaaa", "adescription": "2"}, "files": {"enabled": False}},
    )
    record_b1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {**required_rdm_metadata, "title": "kkkkkkkkk", "bdescription": "3"},
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, record_a1["id"])
    rdm_records_service.publish(identity_simple, record_a2["id"])
    rdm_records_service.publish(identity_simple, record_b1["id"])

    modela_service.indexer.refresh()
    modelb_service.indexer.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {
            "q": "",
            "sort": "bestmatch",
            "page": 1,
            "size": 10,
            "facets": {"metadata_adescription": ["2"]},
        },
    )
    hits = result.to_dict()["hits"]["hits"]
    assert {h["id"] for h in hits} == {record_a2["id"]}


def test_aggregations_include_model_specific_facet(
    db, rdm_records_service, identity_simple, vocab_fixtures, required_rdm_metadata, search_clear
):
    """An unfiltered search returns aggregations for the merged per-model facet."""
    record_a1 = modela_service.create(
        identity_simple,
        {"metadata": {"title": "x", "adescription": "1"}, "files": {"enabled": False}},
    )
    record_a2 = modela_service.create(
        identity_simple,
        {"metadata": {"title": "y", "adescription": "2"}, "files": {"enabled": False}},
    )
    rdm_records_service.publish(identity_simple, record_a1["id"])
    rdm_records_service.publish(identity_simple, record_a2["id"])
    modela_service.indexer.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    aggs = result.to_dict().get("aggregations", {})
    assert "metadata_adescription" in aggs, "Multiplexed search must aggregate the per-model facet"
    buckets = {b["key"]: b["doc_count"] for b in aggs["metadata_adescription"]["buckets"]}
    assert buckets.get("1") == 1
    assert buckets.get("2") == 1
