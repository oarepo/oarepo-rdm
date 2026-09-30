# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service

from .models import modela, modelb, modelc

modela_service = modela.proxies.current_service
modelb_service = modelb.proxies.current_service
modelc_service = modelc.proxies.current_service


@pytest.fixture
def unified_search_permissions(app, monkeypatch):
    """Use the global RDM policy for ownership and grants in all test models."""
    for model in [modela, modelb, modelc]:
        monkeypatch.setattr(
            model.proxies.current_service.config,
            "permission_policy_cls",
            current_rdm_records_service.config.permission_policy_cls,
        )


def test_description_search(app, db, search_clear, identity_simple):
    _modelc_record0 = modelc_service.create(
        system_identity,
        {"metadata": {"title": "blah", "cdescription": "bbb"}},
    )
    _modelc_record1 = modelc_service.create(
        identity_simple,
        {"metadata": {"title": "blah", "cdescription": "kch"}},
    )
    modelc_record2 = modelc_service.create(
        identity_simple,
        {"metadata": {"title": "aaaaa", "cdescription": "jej"}},
    )
    modelc_service.draft_indexer.refresh()

    result = current_rdm_records_service.search_drafts(
        system_identity,
        {"q": "jej", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()
    assert len(results["hits"]["hits"]) == 1

    rec_id = modelc_record2.data["id"]
    assert rec_id == results["hits"]["hits"][0]["id"]
    assert results["links"]["self"] == "/user/records?page=1&q=jej&size=10&sort=bestmatch"
    assert results["hits"]["hits"][0]["links"]["self"] == f"/modelc/{rec_id}/draft"


@pytest.mark.parametrize("model", [modela, modelb, modelc], ids=["minimal", "basic", "complete"])
@pytest.mark.parametrize("use_global_service", [False, True], ids=["specialized", "global"])
def test_drafts_search_shared_with_me_param(
    app, db, search_clear, users, unified_search_permissions, model, use_global_service
):
    """Sharing filters select owned or granted drafts for every RDM profile."""
    owner, other = users[0], users[1]
    service = model.proxies.current_service
    search_service = current_rdm_records_service if use_global_service else service

    shared = service.create(
        owner.identity,
        {"metadata": {"title": "Shared draft"}},
    )
    own = service.create(
        other.identity,
        {"metadata": {"title": "Own draft"}},
    )
    private = service.create(owner.identity, {"metadata": {"title": "Private draft"}})
    service.access.bulk_create_grants(
        owner.identity,
        shared.id,
        {"grants": [{"subject": {"type": "user", "id": str(other.id)}, "permission": "preview"}]},
    )
    service.draft_indexer.process_bulk_queue()
    service.draft_indexer.refresh()

    assert service.read_draft(other.identity, shared.id).id == shared.id

    no_param_uploads = search_service.search_drafts(other.identity)
    hit_ids = {hit["id"] for hit in no_param_uploads.to_dict()["hits"]["hits"]}
    assert hit_ids == {shared.id, own.id}
    assert private.id not in hit_ids

    # this - confusingly named - parameter is used in invenio ui to limit drafts to those owned by the user
    my_uploads = search_service.search_drafts(other.identity, {"shared_with_me": False})
    assert [hit["id"] for hit in my_uploads.to_dict()["hits"]["hits"]] == [own.id]

    shared_with_me = search_service.search_drafts(other.identity, {"shared_with_me": True})
    assert [hit["id"] for hit in shared_with_me.to_dict()["hits"]["hits"]] == [shared.id]


@pytest.mark.parametrize("shared_with_me", [None, False, True], ids=["all-accessible", "owned", "shared"])
def test_global_drafts_search_uses_model_fields_with_sharing_filter(
    app, db, search_clear, users, unified_search_permissions, shared_with_me
):
    """Each delegated draft query searches its model's default fields."""
    owner, other = users[0], users[1]
    owned_ids = set()
    shared_ids = set()

    for model, description_field in [(modela, "adescription"), (modelb, "bdescription"), (modelc, "cdescription")]:
        service = model.proxies.current_service
        data = {"metadata": {"title": "Draft", description_field: "needle"}}
        own = service.create(other.identity, data)
        shared = service.create(owner.identity, data)
        service.create(owner.identity, data)
        service.create(other.identity, {"metadata": {"title": "Draft", description_field: "unrelated"}})
        service.access.bulk_create_grants(
            owner.identity,
            shared.id,
            {"grants": [{"subject": {"type": "user", "id": str(other.id)}, "permission": "preview"}]},
        )
        service.draft_indexer.process_bulk_queue()
        service.draft_indexer.refresh()
        owned_ids.add(own.id)
        shared_ids.add(shared.id)

    params = {"q": "needle"}
    if shared_with_me is not None:
        params["shared_with_me"] = shared_with_me
    result = current_rdm_records_service.search_drafts(other.identity, params)
    expected_ids = owned_ids | shared_ids
    if shared_with_me is not None:
        expected_ids = shared_ids if shared_with_me else owned_ids
    assert {hit["id"] for hit in result.to_dict()["hits"]["hits"]} == expected_ids
