#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test access settings indexing: model-specific vs global (delegating) service."""

from __future__ import annotations

from io import BytesIO

from tests.models import modela

modela_service = modela.proxies.current_service


def _create_versioned_record(service, user) -> tuple[str, str]:
    """Create a record with two published versions, return (v1_pid, v2_pid)."""
    draft_v1 = service.create(
        user.identity,
        data={
            "$schema": "local://modela-v1.0.0.json",
            "metadata": {"title": "Version 1", "adescription": "first"},
            "files": {"enabled": True},
            "access": {"record": "restricted", "files": "restricted"},
        },
    )
    v1_id = draft_v1.id

    service.draft_files.init_files(user.identity, v1_id, data=[{"key": "test.pdf"}])
    service.draft_files.set_file_content(user.identity, v1_id, "test.pdf", BytesIO(b"v1 content"))
    service.draft_files.commit_file(user.identity, v1_id, "test.pdf")

    record_v1 = service.publish(user.identity, v1_id)
    v1_pid = record_v1.id

    new_draft = service.new_version(user.identity, v1_pid)
    v2_id = new_draft.id
    service.import_files(user.identity, v2_id)

    data_v2 = new_draft.data
    data_v2["metadata"]["title"] = "Version 2"
    service.update_draft(user.identity, v2_id, data_v2)

    record_v2 = service.publish(user.identity, v2_id)
    v2_pid = record_v2.id

    modela_service.indexer.refresh()
    return v1_pid, v2_pid


SETTINGS_ENABLED = {
    "allow_user_requests": True,
    "allow_guest_requests": True,
    "accept_conditions_text": "Please explain why you need access.",
    "secret_link_expiration": 30,
}


def _get_settings_from_search(service, user) -> list[tuple[str, dict]]:
    """Return list of (record_id, settings_dict) from search hits."""
    modela_service.indexer.refresh()
    hits = list(service.search(user.identity))
    return [(hit["id"], hit.get("parent", {}).get("access", {}).get("settings", {})) for hit in hits]


def test_access_settings_via_model_specific_service(
    db,
    rdm_records_service,
    users,
    location,
    search_clear,
):
    """Update access settings via the model-specific access service.

    The model-specific RecordAccessService has the correct record_cls
    (ModelaRecord with ModelaRecordMetadata), so ParentRecordCommitOp
    finds all sibling versions via get_records_by_parent and bulk-indexes them.
    """
    user = users[0]
    service = rdm_records_service
    v1_pid, v2_pid = _create_versioned_record(service, user)

    # Use the MODEL-SPECIFIC access service directly
    model_access_service = modela_service.access
    model_access_service.update_access_settings(user.identity, v1_pid, SETTINGS_ENABLED)

    # Verify: the model-specific service correctly enqueues siblings for reindexing.
    # Process the queue and refresh to make changes visible in search.
    modela_service.indexer.process_bulk_queue()

    # DB reads should reflect the settings on both versions (parent is shared)
    read_v1 = service.read(user.identity, v1_pid)
    read_v2 = service.read(user.identity, v2_pid)
    assert read_v1.data["parent"]["access"]["settings"]["allow_user_requests"] is True
    assert read_v2.data["parent"]["access"]["settings"]["allow_user_requests"] is True

    # Search results should also reflect the updated settings
    search_hits = _get_settings_from_search(service, user)
    assert len(search_hits) >= 1
    for record_id, settings in search_hits:
        assert settings.get("allow_user_requests") is True, (
            f"Record {record_id}: expected allow_user_requests=True in search, got {settings}"
        )


def test_access_settings_via_global_delegating_service(
    db,
    rdm_records_service,
    users,
    location,
    search_clear,
):
    """Update access settings via the global DelegatingRecordAccessService.

    The delegating service delegates to the model-specific access service,
    which uses the correct record_cls. ParentRecordCommitOp then finds all
    sibling versions via get_records_by_parent and enqueues them for reindexing.
    After processing the bulk queue, search results reflect the updated settings.
    """
    user = users[0]
    service = rdm_records_service
    v1_pid, v2_pid = _create_versioned_record(service, user)
    # This shouldn't work with rdm_records_service bc of invenio_indexer.api.RecordIndexer._index_action
    modela_service.indexer.process_bulk_queue()

    search_hits = _get_settings_from_search(service, user)
    for _, settings in search_hits:
        assert settings.get("allow_user_requests") is False

    # Use the GLOBAL delegating access service (what the global /records endpoint uses)
    service.access.update_access_settings(user.identity, v1_pid, SETTINGS_ENABLED)

    # Process the bulk queue so that ParentRecordCommitOp's post_commit reindexing takes effect
    modela_service.indexer.process_bulk_queue()

    # DB reads should reflect the settings on both versions (parent is shared)
    read_v1 = service.read(user.identity, v1_pid)
    read_v2 = service.read(user.identity, v2_pid)
    assert read_v1.data["parent"]["access"]["settings"]["allow_user_requests"] is True
    assert read_v2.data["parent"]["access"]["settings"]["allow_user_requests"] is True

    # Search results should also reflect the updated settings
    search_hits = _get_settings_from_search(service, user)
    assert len(search_hits) >= 1
    for record_id, settings in search_hits:
        assert settings.get("allow_user_requests") is True, (
            f"Record {record_id}: expected allow_user_requests=True in search, got {settings}"
        )
