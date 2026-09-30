# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for delegating service classes."""

from __future__ import annotations

import pytest
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records_resources.services.errors import PermissionDeniedError

from .models import modela, modelb

modela_service = modela.proxies.current_service
modelb_service = modelb.proxies.current_service


@pytest.fixture
def published_records(identity_simple, vocab_fixtures, required_rdm_metadata):
    """Create and publish one record from modela and one from modelb."""

    def _publish(service, metadata):
        data = {
            "metadata": {**required_rdm_metadata, **metadata},
            "files": {"enabled": False},
        }
        draft = service.create(identity_simple, data)
        return service.publish(identity_simple, draft["id"])

    rec_a = _publish(modela_service, {"title": "Model A record", "adescription": "desc_a"})
    rec_b = _publish(modelb_service, {"title": "Model B record", "bdescription": "desc_b"})
    return rec_a, rec_b


def test_permission_policy_delegates_to_model(
    db,
    rdm_records_service,
    identity_simple,
    published_records,
    search_clear,
):
    """Test that permission_policy delegates to the specialized model's policy.

    modela uses PermissionPolicyWithModelAPermission which defines can_model_a_specific_action.
    modelb uses the default EveryonePermissionPolicy which does not have this action.
    """
    rec_a, rec_b = published_records

    record_a = rec_a._record
    record_b = rec_b._record

    assert rdm_records_service.review.check_permission(
        identity_simple,
        "model_a_specific_action",
        record=record_a,
    )

    assert not rdm_records_service.review.check_permission(
        identity_simple,
        "model_a_specific_action",
        record=record_b,
    )


def test_pid_resolve_delegates_to_model(
    db,
    rdm_records_service,
    identity_simple,
    published_records,
    search_clear,
):
    rec_a, _rec_b = published_records
    doi = PersistentIdentifier.create(
        pid_type="doi",
        pid_value="10.1234/model-a",
        status=PIDStatus.REGISTERED,
        object_type="rec",
        object_uuid=rec_a._record.id,
    )

    resolved = rdm_records_service.pids.resolve(identity_simple, doi.pid_value, doi.pid_type)

    assert resolved.id == rec_a.id
    assert isinstance(resolved._record, modela.Record)


# these would be better tested by adding some specific component/action to the parent
def test_component_delegates_to_model(
    db, rdm_records_service, identity_simple, published_records, capsys, search_clear
):
    draft = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            "files": {"enabled": False},
        },
    )

    rdm_records_service.review.run_components(
        "create_review",
        identity_simple,
        record=draft._record,
    )

    captured = capsys.readouterr()
    assert "review created in specialized service component" in captured.out


def test_run_components_without_record_uses_parent(
    db,
    rdm_records_service,
    identity_simple,
    capsys,
    search_clear,
):

    modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            "files": {"enabled": False},
        },
    )

    rdm_records_service.review.run_components("create_review", identity_simple)

    captured = capsys.readouterr()
    assert "review created in original rdm service component" in captured.out
    assert "review created in specialized service component" not in captured.out


def test_permission_policy_without_record_uses_parent(
    db,
    rdm_records_service,
    identity_simple,
    published_records,
    search_clear,
):
    _rec_a, _rec_b = published_records

    with pytest.raises(PermissionDeniedError):
        assert rdm_records_service.access.require_permission(
            identity_simple,
            "model_a_specific_action",
        )
