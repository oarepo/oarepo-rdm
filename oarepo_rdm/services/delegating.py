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

from typing import TYPE_CHECKING, cast, override

from invenio_rdm_records.services.access.service import RecordAccessService
from invenio_rdm_records.services.pids.service import PIDsService
from invenio_rdm_records.services.review.service import ReviewService
from oarepo_runtime import current_runtime

if TYPE_CHECKING:
    from typing import Any

    from invenio_rdm_records.services.services import RDMRecordService
    from invenio_records_permissions.policies.base import BasePermissionPolicy
    from invenio_records_resources.services.base.service import Service as InvenioService
else:
    InvenioService = object


class DelegationToSpecializedServiceMixin(InvenioService):
    """Mixin for delegating running components and permission checks to specialized model services."""

    def _get_specialized_service(self, pid_value: str) -> RDMRecordService:
        """Get a specialized service based on the pid_value of the record."""
        pid_type = current_runtime.find_pid_type_from_pid(pid_value)
        return cast("RDMRecordService", current_runtime.model_by_pid_type[pid_type].service)

    @override
    def run_components(self, action: str, *args: Any, **kwargs: Any) -> None:
        if "record" in kwargs:
            record = kwargs["record"]
            specialized = self._get_specialized_service(record.pid.pid_value)
            if specialized is not self:
                specialized.run_components(action, *args, **kwargs)
        super().run_components(action, *args, **kwargs)

    @override
    def permission_policy(self, action_name: str, **kwargs: Any) -> BasePermissionPolicy:
        if "record" in kwargs:
            return self._get_specialized_service(kwargs["record"].pid.pid_value).permission_policy(
                action_name, **kwargs
            )
        return super().permission_policy(action_name, **kwargs)


class DelegatingReviewService(DelegationToSpecializedServiceMixin, ReviewService):
    """Delegating review service."""


class DelegatingRecordAccessService(DelegationToSpecializedServiceMixin, RecordAccessService):
    """Delegating access service."""


class DelegatingPIDsService(DelegationToSpecializedServiceMixin, PIDsService):
    """Delegating access service."""
