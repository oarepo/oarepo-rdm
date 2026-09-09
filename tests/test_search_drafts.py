#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service

from .models import modela, modelb, modelc

modela_service = modela.proxies.current_service
modelb_service = modelb.proxies.current_service
modelc_service = modelc.proxies.current_service


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


def test_drafts_search_shared_with_me_param(app, db, search_clear, users):
    """Test whether search_drafts() works with shared_with_me param."""
    owner, other = users[0], users[1]

    shared = modelc_service.create(
        owner.identity,
        {"metadata": {"title": "blah", "cdescription": "bbb"}},
    )
    own = modelc_service.create(
        other.identity,
        {"metadata": {"title": "blah", "cdescription": "kch"}},
    )
    modelc_service.access.bulk_create_grants(
        owner.identity,
        shared.id,
        {"grants": [{"subject": {"type": "user", "id": str(other.id)}, "permission": "preview"}]},
    )
    modelc_service.draft_indexer.refresh()

    assert modelc_service.read_draft(other.identity, shared.id).id == shared.id

    no_param_uploads = modelc_service.search_drafts(other.identity)
    assert len(no_param_uploads.to_dict()["hits"]["hits"]) == 2

    # this - confusingly named - parameter is used in invenio ui to limit drafts to those owned by the user
    my_uploads = modelc_service.search_drafts(other.identity, {"shared_with_me": False})
    assert [hit["id"] for hit in my_uploads.to_dict()["hits"]["hits"]] == [own.id]

    shared_with_me = modelc_service.search_drafts(other.identity, {"shared_with_me": True})
    assert [hit["id"] for hit in shared_with_me.to_dict()["hits"]["hits"]] == [shared.id]
