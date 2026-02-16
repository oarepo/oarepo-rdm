#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from .models import modela, modelb, modelc

modela_service = modela.proxies.current_service
modelb_service = modelb.proxies.current_service
modelc_service = modelc.proxies.current_service


def test_description_search(rdm_records_service, identity_simple, search_clear):
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            "files": {"enabled": False},
        },
    )
    modela_record2 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "aaaaa", "adescription": "jej"},
            "files": {"enabled": False},
        },
    )
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "bdescription": "blah"},
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.publish(identity_simple, modela_record2["id"])
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    modela_service.indexer.refresh()
    modelb_service.indexer.refresh()
    modela_service.draft_indexer.refresh()
    modelb_service.draft_indexer.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "jej", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()
    assert len(results["hits"]["hits"]) == 1
    hit_ids = {r["id"] for r in results["hits"]["hits"]}

    assert (
        modela_record2["id"] in hit_ids
    )  # TODO: modela_record2.data in results["hits"]["hits"] - those are not the same but that's ok?
    assert modelb_record1["id"] not in hit_ids
    assert modela_record1["id"] not in hit_ids


def test_basic_search(rdm_records_service, identity_simple, search_clear):
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            "files": {"enabled": False},
        },
    )
    modela_record2 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "aaaaa", "adescription": "jej"},
            "files": {"enabled": False},
        },
    )
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "bdescription": "blah"},
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.publish(identity_simple, modela_record2["id"])
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    modela_service.indexer.refresh()
    modelb_service.indexer.refresh()
    modela_service.draft_indexer.refresh()
    modelb_service.draft_indexer.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()

    assert len(results["hits"]["hits"]) == 2

    hit_ids = {r["id"] for r in results["hits"]["hits"]}

    assert modela_record2["id"] not in hit_ids
    assert modelb_record1["id"] in hit_ids
    assert modela_record1["id"] in hit_ids


def test_mixed_with_drafts(rdm_records_service, identity_simple, search_clear):
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            "files": {"enabled": False},
        },
    )
    modela_record2 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "aaaaa", "adescription": "jej"},
            "files": {"enabled": False},
        },
    )
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "bdescription": "blah"},
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    modela_service.indexer.refresh()
    modelb_service.indexer.refresh()
    modela_service.draft_indexer.refresh()
    modelb_service.draft_indexer.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()

    assert len(results["hits"]["hits"]) == 2

    hit_ids = {r["id"] for r in results["hits"]["hits"]}

    assert modela_record2["id"] not in hit_ids
    assert modelb_record1["id"] in hit_ids
    assert modela_record1["id"] in hit_ids


def test_record_and_edited_draft(rdm_records_service, identity_simple, search_clear):
    # should we find both record and draft?
    # edited draft is not found bc it does not have $schema in opensearch
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.edit(identity_simple, modela_record1["id"])

    modela_service.indexer.refresh()
    modelb_service.indexer.refresh()
    modela_service.draft_indexer.refresh()
    modelb_service.draft_indexer.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()

    assert len(results["hits"]["hits"]) == 1

    hit_ids = {r["id"] for r in results["hits"]["hits"]}

    assert modela_record1["id"] in hit_ids


def test_links(rdm_records_service, identity_simple, search_clear):
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "bdescription": "blah"},
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    modelb_service.indexer.refresh()
    modelb_service.draft_indexer.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 1, "size": 20, "facets": {}},
    )
    results = result.to_dict()

    assert results["links"]["self"] == "http://localhost/records?page=1&q=blah&size=20&sort=bestmatch"
    assert results["hits"]["hits"][0]["links"]["self"].startswith("http://localhost/modelb/")


def test_second_page(rdm_records_service, identity_simple, search_clear):
    for r in range(10):
        draft = modelb_service.create(
            identity_simple,
            {
                "metadata": {"title": f"blah {r}", "bdescription": "blah"},
                "files": {"enabled": False},
            },
        )
        rdm_records_service.publish(identity_simple, draft["id"])
    modelb_service.indexer.refresh()
    modelb_service.draft_indexer.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 1, "size": 5, "facets": {}},
    )
    results = result.to_dict()

    assert results["links"]["self"] == "http://localhost/records?page=1&q=blah&size=5&sort=bestmatch"
    assert results["links"]["next"] == "http://localhost/records?page=2&q=blah&size=5&sort=bestmatch"

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 2, "size": 5, "facets": {}},
    )
    results = result.to_dict()

    assert results["links"]["self"] == "http://localhost/records?page=2&q=blah&size=5&sort=bestmatch"
    assert results["links"]["prev"] == "http://localhost/records?page=1&q=blah&size=5&sort=bestmatch"


def test_zero_hits(rdm_records_service, identity_simple, search_clear):
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            "files": {"enabled": False},
        },
    )
    modela_record2 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "aaaaa", "adescription": "blah"},
            "files": {"enabled": False},
        },
    )
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "bdescription": "blah"},
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.publish(identity_simple, modela_record2["id"])
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    modela_service.indexer.refresh()
    modelb_service.indexer.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "jej", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()

    assert len(results["hits"]["hits"]) == 0


def test_multiple_from_one_schema(rdm_records_service, identity_simple, search_clear):
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            "files": {"enabled": False},
        },
    )
    modela_record2 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "aaaaa", "adescription": "blah"},
            "files": {"enabled": False},
        },
    )
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "kkkkkkkkk", "bdescription": "kkkkk"},
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.publish(identity_simple, modela_record2["id"])
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    modela_service.indexer.refresh()
    modelb_service.indexer.refresh()
    modela_service.draft_indexer.refresh()
    modelb_service.draft_indexer.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()
    hit_ids = {r["id"] for r in results["hits"]["hits"]}

    assert len(results["hits"]["hits"]) == 2
    assert modelb_record1["id"] not in hit_ids


def test_facets(rdm_records_service, identity_simple, search_clear):
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "1"},
            "files": {"enabled": False},
        },
    )
    modela_record2 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "aaaaa", "adescription": "2"},
            "files": {"enabled": False},
        },
    )
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "kkkkkkkkk", "bdescription": "3"},
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.publish(identity_simple, modela_record2["id"])
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    modela_service.indexer.refresh()
    modelb_service.indexer.refresh()
    modela_service.draft_indexer.refresh()
    modelb_service.draft_indexer.refresh()

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
    results = result.to_dict()
    assert len(results["hits"]["hits"]) == 1
    hit_ids = {r["id"] for r in results["hits"]["hits"]}
    assert modela_record2["id"] in hit_ids


def test_search_eligible_services_permissions(rdm_records_service, identity_simple, search_clear):
    eligible_services = rdm_records_service._search_eligible_services(  # noqa: SLF001  # because in tests
        identity_simple, permission_action="model_a_specific_action"
    )
    assert "local://modela-v1.0.0.json" in eligible_services
    assert len(eligible_services) == 1
