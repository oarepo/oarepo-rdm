#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Test for MultiplexingSchema."""

from __future__ import annotations

from oarepo_rdm.services.config import MultiplexingSchema
from tests.models import modela, modelb


def test_multiplexing_schema_load_single(db, identity_simple, search_clear):
    """Test MultiplexingSchema.load() with a single record (many=False)."""
    modela_service = modela.proxies.current_service

    # Create a draft to have valid data
    _ = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "Test A", "adescription": "desc"},
            "files": {"enabled": False},
        },
    )

    # Get the raw data with $schema
    data = {
        "$schema": "local://modela-v1.0.0.json",
        "metadata": {"title": "Test Load", "adescription": "load desc"},
    }

    schema = MultiplexingSchema(context={"identity": identity_simple})
    result = schema.load(data)

    # The result should be the loaded data (tuple from ServiceSchemaWrapper)
    assert result is not None


def test_multiplexing_schema_load_many(db, identity_simple, search_clear):
    """Test MultiplexingSchema.load() with many=True."""
    data_list = [
        {
            "$schema": "local://modela-v1.0.0.json",
            "metadata": {"title": "Test A1", "adescription": "desc1"},
        },
        {
            "$schema": "local://modela-v1.0.0.json",
            "metadata": {"title": "Test A2", "adescription": "desc2"},
        },
    ]

    schema = MultiplexingSchema(context={"identity": identity_simple})
    result = schema.load(data_list, many=True)

    assert isinstance(result, list)
    assert len(result) == 2


def test_multiplexing_schema_dump_single(db, identity_simple, search_clear):
    """Test MultiplexingSchema.dump() with a single record (many=False)."""
    modela_service = modela.proxies.current_service

    # Create a draft
    draft = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "Test Dump", "adescription": "dump desc"},
            "files": {"enabled": False},
        },
    )

    # Get the actual record object
    record = draft._record  # noqa: SLF001

    schema = MultiplexingSchema(context={"identity": identity_simple})
    result = schema.dump(record)

    assert isinstance(result, dict)
    assert "$schema" in result
    assert result["$schema"] == "local://modela-v1.0.0.json"


def test_multiplexing_schema_dump_many(db, identity_simple, search_clear):
    """Test MultiplexingSchema.dump() with many=True."""
    modela_service = modela.proxies.current_service
    modelb_service = modelb.proxies.current_service

    # Create drafts
    draft_a = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "Test A", "adescription": "desc a"},
            "files": {"enabled": False},
        },
    )
    draft_b = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "Test B", "bdescription": "desc b"},
            "files": {"enabled": False},
        },
    )

    records = [draft_a._record, draft_b._record]  # noqa: SLF001

    schema = MultiplexingSchema(context={"identity": identity_simple})
    result = schema.dump(records, many=True)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["$schema"] == "local://modela-v1.0.0.json"
    assert result[1]["$schema"] == "local://modelb-v1.0.0.json"
