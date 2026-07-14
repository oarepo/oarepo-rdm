#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for the collections records service search override.

``OARepoCollectionsRecordsService.search`` searches across every record for the
designated global-collections community (``INVENIO_COLLECTIONS_COMMUNITY_SLUG``),
instead of only the records tagged with the holder community.

Only the global-collections branch is exercised end to end: the community-scoped
fallback (``super().search``) would require a record that is an actual community
member, which needs the communities/workflows/requests preset stack (create-time
community assignment plus the ``rdm_parents_community`` linkage).
"""

from __future__ import annotations

from typing import Any

import pytest
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_community_records_service

from oarepo_rdm.services.collections import OARepoCollectionsRecordsService

from .models import modela

modela_service = modela.proxies.current_service

GLOBAL_SLUG = "global-collections"

# modela is a minimal RDM model: only title + adescription, no files.
_MODELA_DATA = {"metadata": {"title": "blah", "adescription": "x"}, "files": {"enabled": False}}


@pytest.fixture
def collections_service() -> OARepoCollectionsRecordsService:
    """Return a real collections service sharing the community-records config."""
    return OARepoCollectionsRecordsService(config=current_community_records_service.config)


def _publish() -> dict[str, Any]:
    """Publish a modela record (not a member of any community)."""
    draft = modela_service.create(system_identity, _MODELA_DATA)
    return modela_service.publish(system_identity, draft["id"]).to_dict()


def test_global_collections_community_spans_all_records(
    app, collections_service, community_get_or_create, community_owner, search_clear, monkeypatch
):
    """The global-collections community search returns records from no community at all."""
    monkeypatch.setitem(app.config, "INVENIO_COLLECTIONS_COMMUNITY_SLUG", GLOBAL_SLUG)
    global_community = community_get_or_create(community_owner, slug=GLOBAL_SLUG)

    record_1 = _publish()
    record_2 = _publish()

    modela_service.indexer.refresh()
    result = collections_service.search(system_identity, global_community.slug)
    hits = {hit["id"] for hit in result.to_dict()["hits"]["hits"]}

    assert {record_1["id"], record_2["id"]} <= hits
