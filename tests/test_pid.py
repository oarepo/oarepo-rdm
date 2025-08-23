#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from typing import Any, override

import pytest
from invenio_access.permissions import system_identity
from invenio_drafts_resources.records.api import DraftRecordIdProviderV2
from invenio_pidstore.errors import PIDAlreadyExists
from invenio_rdm_records.records.api import RDMDraft
from invenio_records.systemfields.base import SystemFieldsExt
from oarepo_runtime.records.pid_providers import UniversalPIDMixin

FAKE_PID = "xavsd-8adfd"


class ModelaFakePIDProvider(UniversalPIDMixin, DraftRecordIdProviderV2):
    """Fake PID provider for modela."""

    pid_type = "modela"  # type: ignore[assignment] # no typing in invenio

    @override
    @classmethod
    def generate_id(cls, options: Any = None) -> str:
        return FAKE_PID


class ModelbFakePIDProvider(DraftRecordIdProviderV2):
    """Fake PID provider for modelb."""

    pid_type = "modelb"  # type: ignore[assignment] # no typing in invenio

    @override
    @classmethod
    def generate_id(cls, options: Any = None) -> str:
        return FAKE_PID


class ModelcFakePIDProvider(UniversalPIDMixin, DraftRecordIdProviderV2):
    """Fake PID provider for modelc."""

    pid_type = "modelc"  # type: ignore[assignment] # no typing in invenio

    @override
    @classmethod
    def generate_id(cls, options: Any = None) -> str:
        return FAKE_PID


def test_pid(model_c, search_clear):
    modelc_record1 = model_c.proxies.current_service.create(
        system_identity,
        {"metadata": {"title": "blah", "cdescription": "kch"}},
    )
    id_ = modelc_record1["id"]
    draft = RDMDraft.pid.resolve(id_)
    assert isinstance(draft, model_c.Draft)


def monkeypatch_pid_provider(cls, provider, monkeypatch):
    monkeypatch.setattr(cls.pid.field, "_provider", provider)
    for extension in cls._extensions:
        if isinstance(extension, SystemFieldsExt):
            monkeypatch.setattr(extension.declared_fields["pid"], "_provider", provider)


def test_universal_provider(
    model_a,
    model_b,
    model_c,
    rdm_records_service,
    identity_simple,
    monkeypatch,
    search_clear,
):
    recorda = rdm_records_service.create(
        identity_simple,
        data={
            "$schema": "local://modela-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    recordb = rdm_records_service.create(
        identity_simple,
        data={
            "$schema": "local://modelb-v1.0.0.json",
            "files": {"enabled": False},
        },
    )

    monkeypatch_pid_provider(model_a.Draft, ModelaFakePIDProvider, monkeypatch)
    monkeypatch_pid_provider(model_b.Draft, ModelbFakePIDProvider, monkeypatch)
    monkeypatch_pid_provider(model_c.Draft, ModelcFakePIDProvider, monkeypatch)

    recorda = rdm_records_service.create(
        identity_simple,
        data={
            "$schema": "local://modela-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    # record does not use collective check
    recordb = rdm_records_service.create(
        identity_simple,
        data={
            "$schema": "local://modelb-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    assert recorda["id"] == recordb["id"]
    with pytest.raises(PIDAlreadyExists):
        rdm_records_service.create(
            identity_simple,
            data={
                "$schema": "local://modelc-v1.0.0.json",
                "files": {"enabled": False},
            },
        )
