#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""What ``check_fully_overridden`` covers.

The decorator is the safety net for the delegation design: every public method of the
base service is supposed to be either delegated, overridden, or listed in
``pass_through``, and anything left over stops the class from being built.

It used to be a no-op for two independent reasons:

* it compared ``cls.__dict__.get(name) is value``, and a method that was simply *not*
  overridden is absent from ``cls.__dict__`` -- so the comparison was ``None is value``.
  Only a verbatim ``method = Base.method`` alias tripped it.
* it walked ``vars(base_class)`` -- one class ``__dict__``, not the MRO -- so everything
  ``RecordService``, ``DraftsRecordService`` and ``Service`` contribute was invisible.

Properties still escape the guard for a third reason -- ``callable(property)`` is False --
which is covered in ``tests/test_global_service_indexing.py``.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest
from invenio_rdm_records.services.access.service import RecordAccessService
from invenio_rdm_records.services.pids.service import PIDsService
from invenio_rdm_records.services.review.service import ReviewService
from invenio_rdm_records.services.services import RDMRecordService
from invenio_records_resources.services.errors import PermissionDeniedError

from oarepo_rdm.services.delegating import (
    DelegatingPIDsService,
    DelegatingRecordAccessService,
    DelegatingReviewService,
    delegate_to_specialized_service_access,
    delegate_to_specialized_service_pids,
    delegate_to_specialized_service_review,
    pass_through_record_service,
    pass_through_service_access,
    pass_through_service_pids,
)
from oarepo_rdm.services.service import (
    OARepoRDMService,
    check_fully_overridden,
    delegate_to_specialized_service,
    delegate_to_specialized_service_rdm,
    pass_through,
    pass_through_rdm,
)
from tests.models import modela

if TYPE_CHECKING:
    from invenio_access.permissions import Identity
    from invenio_records_resources.records.api import Record

modela_service = modela.proxies.current_service


def test_guard_rejects_an_alias_and_accepts_a_real_override():

    class Base:
        def method(self) -> None: ...

    class Aliasing(Base):
        method = Base.method

    class Overriding(Base):
        def method(self) -> None: ...

    with pytest.raises(TypeError, match="is not overridden"):
        check_fully_overridden((), (), Base)(Aliasing)

    assert check_fully_overridden((), (), Base)(Overriding) is Overriding


def test_guard_rejects_a_method_left_unimplemented():
    """The case the guard exists for: a subclass that forgot to override a base method."""

    class Base:
        def method(self) -> None: ...

    class Inheriting(Base):
        pass

    with pytest.raises(TypeError, match="is not overridden"):
        check_fully_overridden((), (), Base)(Inheriting)


def test_guard_looks_past_the_immediate_base_class():
    """A method the base class itself inherits is unclassified too, and must be checked.

    Written in the alias shape, so the class-dict lookup of the previous test is not
    what fails here -- ``vars(Base)`` simply does not contain ``method``.
    """

    class Grandparent:
        def method(self) -> None: ...

    class Base(Grandparent):
        pass

    class Inheriting(Base):
        method = Grandparent.method

    with pytest.raises(TypeError, match="is not overridden"):
        check_fully_overridden((), (), Base)(Inheriting)


@pytest.mark.parametrize(
    ("service", "base", "classified_pass_through", "classified_delegate"),
    [
        (
            OARepoRDMService,
            RDMRecordService,
            pass_through | pass_through_rdm,
            delegate_to_specialized_service | delegate_to_specialized_service_rdm,
        ),
        (
            DelegatingReviewService,
            ReviewService,
            pass_through | pass_through_record_service,
            delegate_to_specialized_service | delegate_to_specialized_service_review,
        ),
        (
            DelegatingRecordAccessService,
            RecordAccessService,
            pass_through | pass_through_service_access,
            delegate_to_specialized_service | delegate_to_specialized_service_access,
        ),
        (
            DelegatingPIDsService,
            PIDsService,
            pass_through | pass_through_service_pids,
            delegate_to_specialized_service | delegate_to_specialized_service_pids,
        ),
    ],
    ids=["records", "review", "access", "pids"],
)
def test_no_base_service_method_is_silently_inherited(service, base, classified_pass_through, classified_delegate):
    """Every public method of each base service is delegated, overridden, or passed through.

    The sub-services subclass the generic record service, so the base surface reaches far
    past their own ``__dict__``.
    """
    guard = check_fully_overridden(classified_pass_through, classified_delegate, base)
    assert guard(service) is service


class _RecordingQuotaPolicy:
    """Quota increase policy that records the records it was asked about and denies."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def evaluate(self, identity: Identity, record: Record) -> dict[str, Any]:  # noqa ARG002
        self.calls.append(record.pid.pid_value)
        return {"immediate_quota_increase": SimpleNamespace(enabled=False, allowed=False)}


@pytest.mark.parametrize(
    "use_global_service",
    [False, True],
    ids=["specialized_service", "global_service"],
)
def test_quota_increase_evaluates_the_model_policy(
    db,
    monkeypatch,
    rdm_records_service,
    identity_simple,
    search_clear,
    use_global_service,
):
    """``quota_increase`` must evaluate the policy of the model owning the record.

    Inherited as-is it ran on the multiplexer: ``self.config`` is
    ``OARepoRDMServiceConfig``, so a model that configures its own quota policy was
    bypassed the moment the call arrived through the global service.
    """
    draft = modela_service.create(
        identity_simple,
        {"metadata": {"title": "Test record"}, "files": {"enabled": True}},
    )

    model_policy = _RecordingQuotaPolicy()
    global_policy = _RecordingQuotaPolicy()
    # raising=False: FromConfig has no class-level __get__, so the inherited attribute is
    # invisible to a plain getattr on the config class.
    monkeypatch.setattr(type(modela_service.config), "quota_increase_policy", model_policy, raising=False)
    monkeypatch.setattr(type(rdm_records_service.config), "quota_increase_policy", global_policy, raising=False)

    service = rdm_records_service if use_global_service else modela_service
    with pytest.raises(PermissionDeniedError):
        service.quota_increase(identity_simple, draft.id, {"quota_size": 1})

    assert model_policy.calls == [draft.id]
    assert global_policy.calls == []
