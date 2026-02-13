#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for delegating service classes."""

from __future__ import annotations

import pytest
from invenio_records_resources.services.errors import PermissionDeniedError

from .models import modela, modelb

modela_service = modela.proxies.current_service
modelb_service = modelb.proxies.current_service


@pytest.fixture
def published_records(identity_simple, vocab_fixtures, required_rdm_metadata):
    """Create and publish one record from modela and one from modelb."""

    def _publish(service, metadata):  # noqa: ANN202
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

    # Resolve the actual record objects for passing as kwargs
    record_a = rec_a._record  # noqa: SLF001
    record_b = rec_b._record  # noqa: SLF001

    # modela's policy has can_model_a_specific_action => should succeed
    assert rdm_records_service.access.check_permission(
        identity_simple,
        "model_a_specific_action",
        record=record_a,
    )

    # modelb's policy does NOT have can_model_a_specific_action => should fail
    assert not rdm_records_service.access.check_permission(
        identity_simple,
        "model_a_specific_action",
        record=record_b,
    )

    # Also verify via require_permission
    rdm_records_service.access.require_permission(
        identity_simple,
        "model_a_specific_action",
        record=record_a,
    )

    with pytest.raises(PermissionDeniedError):
        rdm_records_service.access.require_permission(
            identity_simple,
            "model_a_specific_action",
            record=record_b,
        )


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
        record=draft._record,  # noqa: SLF001
    )

    captured = capsys.readouterr()
    assert "review created" in captured.out


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
    assert "review created" not in captured.out


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
