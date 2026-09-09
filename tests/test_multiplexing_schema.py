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

from types import SimpleNamespace
from typing import Any, ClassVar

import marshmallow as ma
from flask_principal import Identity
from invenio_access.permissions import system_identity
from invenio_records_resources.services.records.schema import ServiceSchemaWrapper
from marshmallow_utils.context import context_schema
from marshmallow_utils.permissions import FieldPermissionsMixin

import oarepo_rdm.services.config as service_config
from oarepo_rdm.services.config import MultiplexingSchema
from tests.models import modela, modelb


class _ProtectedRecordSchema(FieldPermissionsMixin, ma.Schema):
    schema = ma.fields.String(data_key="$schema")
    internal_notes = ma.fields.List(ma.fields.String())

    field_dump_permissions: ClassVar[dict[str, str]] = {"internal_notes": "manage_internal"}


class _SystemOnlyPermissionPolicy:
    def __init__(self, action: str, **kwargs: Any) -> None:
        self.action = action
        self.context = kwargs

    def allows(self, identity: Identity) -> bool:
        return identity is system_identity


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

    schema = MultiplexingSchema()
    token = context_schema.set({"identity": identity_simple})
    try:
        result = schema.load(data)
    finally:
        context_schema.reset(token)

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

    schema = MultiplexingSchema()
    token = context_schema.set({"identity": identity_simple})
    try:
        result = schema.load(data_list, many=True)
    finally:
        context_schema.reset(token)

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

    schema = MultiplexingSchema()
    token = context_schema.set({"identity": identity_simple})
    try:
        result = schema.dump(record)
    finally:
        context_schema.reset(token)

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

    schema = MultiplexingSchema()
    token = context_schema.set({"identity": identity_simple})
    try:
        result = schema.dump(records, many=True)
    finally:
        context_schema.reset(token)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["$schema"] == "local://modela-v1.0.0.json"
    assert result[1]["$schema"] == "local://modelb-v1.0.0.json"


def test_multiplexing_schema_dump_uses_service_context(monkeypatch):
    """Do not expose a protected field when dumping through the multiplexing service schema.

    ServiceSchemaWrapper supplies the caller context through context_schema rather
    than the Marshmallow schema constructor.  This is the path used in production
    and differs from the direct MultiplexingSchema(context=...) calls above.
    """
    delegated_service = SimpleNamespace(
        config=SimpleNamespace(permission_policy_cls=_SystemOnlyPermissionPolicy),
    )
    delegated_service.schema = ServiceSchemaWrapper(delegated_service, _ProtectedRecordSchema)
    monkeypatch.setattr(
        service_config,
        "current_runtime",
        SimpleNamespace(
            rdm_models_by_schema={
                "local://protected-v1.0.0.json": SimpleNamespace(service=delegated_service),
            }
        ),
    )

    multiplexing_service = SimpleNamespace(
        config=SimpleNamespace(permission_policy_cls=_SystemOnlyPermissionPolicy),
    )
    multiplexing_schema_service_wrapped = ServiceSchemaWrapper(multiplexing_service, MultiplexingSchema)
    identity = Identity("ordinary-user")
    record = {
        "$schema": "local://protected-v1.0.0.json",
        "internal_notes": ["visible only to repository managers"],
    }

    delegated_dump = delegated_service.schema.dump(
        record,
        context={"identity": identity},
    )
    multiplexed_dump = multiplexing_schema_service_wrapped.dump(
        record,
        context={"identity": identity},
    )

    multiplexed_dump_system_identity = multiplexing_schema_service_wrapped.dump(
        record,
        context={"identity": system_identity},
    )

    assert "internal_notes" not in delegated_dump
    assert "internal_notes" not in multiplexed_dump
    assert "internal_notes" in multiplexed_dump_system_identity
