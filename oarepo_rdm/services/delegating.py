#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Invenio services edited to delegate running components and permission checks to specialized model services."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from invenio_db.uow import UnitOfWork, unit_of_work
from invenio_rdm_records.services.access.service import RecordAccessService
from invenio_rdm_records.services.pids.service import PIDsService
from invenio_rdm_records.services.review.service import ReviewService

from oarepo_rdm.services.service import (
    DelegationToSpecializedServiceMixin,
    check_fully_overridden,
    delegate_to_specialized_service,
    pass_through,
    pass_to_specialized_service,
)

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_rdm_records.records.api import RDMDraft, RDMRecord
    from invenio_records_resources.services.records.results import RecordItem

    from invenio_records_permissions.policies.base import BasePermissionPolicy
    from invenio_records_resources.services.base.service import (
        Service as InvenioService,
    )
else:
    InvenioService = object

pass_through_service_access = {
    "link_result_item",
    "link_result_list",
    "grant_result_item",
    "grants_result_list",
    "create_guest_access_request",  # nonstandard way of passing record id
}

delegate_to_specialized_service_access = {
    "get_parent_and_record_or_draft",
    "create_secret_link",
    "read_all_secret_links",
    "read_secret_link",
    "update_secret_link",
    "delete_secret_link",
    "bulk_create_grants",
    "read_grant",
    "update_grant",
    "delete_grant",
    "create_user_access_request",
    "create_guest_access_request_token",
    "update_grant_by_subject",
    "update_access_settings",
    "read_grant_by_subject",
    "read_all_grants_by_subject",
    "delete_grant_by_subject",
    "read_all_grants",
    "request_access",
}

delegate_to_specialized_service_review = {
    "submit",
}

pass_through_service_pids = {
    "invalidate",  # not implemented
}

delegate_to_specialized_service_pids = {
    "create",
    "discard",
    "register_or_update",
    "reserve",
    "resolve",
}


@pass_to_specialized_service(delegate_to_specialized_service | delegate_to_specialized_service_review)
@check_fully_overridden(
    pass_through,
    delegate_to_specialized_service | delegate_to_specialized_service_review,
    ReviewService,
)
class DelegatingReviewService(DelegationToSpecializedServiceMixin, ReviewService):
    """Delegating review service."""

    attribute_on_base_service = "review"

    @unit_of_work()
    @override
    def create(
        self,
        identity: Identity,
        data: dict[str, Any],
        record: RDMRecord | RDMDraft,
        uow: UnitOfWork,
    ) -> RecordItem:
        specialized_service = cast("ReviewService", self._get_specialized_service(str(record.pid.pid_value)))
        return specialized_service.create(identity, data, record, uow)


@pass_to_specialized_service(delegate_to_specialized_service | delegate_to_specialized_service_access)
@check_fully_overridden(
    pass_through | pass_through_service_access,
    delegate_to_specialized_service | delegate_to_specialized_service_access,
    RecordAccessService,
)
class DelegatingRecordAccessService(DelegationToSpecializedServiceMixin, RecordAccessService):
    """Delegating access service."""

    attribute_on_base_service = "access"


@pass_to_specialized_service(delegate_to_specialized_service | delegate_to_specialized_service_pids)
@check_fully_overridden(
    pass_through | pass_through_service_pids,
    delegate_to_specialized_service | delegate_to_specialized_service_pids,
    PIDsService,
)
class DelegatingPIDsService(DelegationToSpecializedServiceMixin, PIDsService):
    """Delegating PIDs service."""

    attribute_on_base_service = "pids"
