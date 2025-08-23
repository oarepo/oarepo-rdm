#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
import pytest
from invenio_pidstore.errors import PIDDoesNotExistError

from .models import modela, modelb, modelc

modela_service = modela.proxies.current_service
modelb_service = modelb.proxies.current_service
modelc_service = modelc.proxies.current_service

ModelaDraft = modela.Draft
ModelbDraft = modelb.Draft

from oarepo_rdm.errors import UndefinedModelError

from .utils import record_from_result


def test_create(rdm_records_service, identity_simple, search_clear):
    with pytest.raises(UndefinedModelError):
        rdm_records_service.create(identity_simple, data={})
    recorda = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modela-v1.0.0.json"}
    )
    recordb = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modelb-v1.0.0.json"}
    )
    with pytest.raises(UndefinedModelError):
        rdm_records_service.create(
            identity_simple,
            data={"$schema": "local://modeld-v1.0.0.json"},
        )
    assert isinstance(record_from_result(recorda), ModelaDraft)
    assert isinstance(record_from_result(recordb), ModelbDraft)


def test_read(rdm_records_service, identity_simple, search_clear):
    sample_draft = modelc_service.create(
        identity_simple,
        {"metadata": {"title": "blah", "cdescription": "kch"}},
    )
    with pytest.raises(PIDDoesNotExistError):
        rdm_records_service.read_draft(identity_simple, "nonsense")
    read_record = rdm_records_service.read_draft(identity_simple, sample_draft["id"])
    assert read_record.data["$schema"] == "local://modelc-v1.0.0.json"


def test_update(rdm_records_service, identity_simple, search_clear):
    sample_draft = modelc_service.create(
        identity_simple,
        {"metadata": {"title": "blah", "cdescription": "kch"}},
    )

    with pytest.raises(PIDDoesNotExistError):
        rdm_records_service.update_draft(
            identity_simple,
            "nonsense",
            {"metadata": {"title": "blah", "cdescription": "lalala"}},
        )

    old_record_data = rdm_records_service.read_draft(
        identity_simple, sample_draft["id"]
    ).data
    updated_record = rdm_records_service.update_draft(
        identity_simple,
        sample_draft["id"],
        {"metadata": {"title": "blah", "cdescription": "lalala"}},
    )
    updated_record_read = rdm_records_service.read_draft(
        identity_simple, sample_draft["id"]
    )
    assert old_record_data["metadata"] == sample_draft["metadata"]
    assert (
        updated_record.data["metadata"]
        == {"title": "blah", "cdescription": "lalala"}
        != old_record_data["metadata"]
    )
    assert updated_record_read.data["metadata"] == updated_record.data["metadata"]
    assert (
        updated_record.data["revision_id"]
        == updated_record_read.data["revision_id"]
        == old_record_data["revision_id"] + 1
    )


def test_delete(rdm_records_service, identity_simple, search_clear):
    sample_draft = modelc_service.create(
        identity_simple,
        {"metadata": {"title": "blah", "cdescription": "kch"}},
    )

    with pytest.raises(PIDDoesNotExistError):
        rdm_records_service.delete_draft(identity_simple, "nonsense")

    to_delete_record = rdm_records_service.read_draft(
        identity_simple, sample_draft["id"]
    )
    assert to_delete_record
    rdm_records_service.delete_draft(identity_simple, sample_draft["id"])
    with pytest.raises(PIDDoesNotExistError):
        rdm_records_service.read_draft(identity_simple, sample_draft["id"])


def test_publish(rdm_records_service, identity_simple, search_clear):
    sample_draft = modelc_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "cdescription": "kch"},
            "files": {"enabled": False},
        },
    )

    _publish = rdm_records_service.publish(identity_simple, sample_draft["id"])
    _record = rdm_records_service.read(identity_simple, sample_draft["id"])
