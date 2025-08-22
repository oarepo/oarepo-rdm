#
# Copyright (C) 2025 CESNET z.s.p.o.
#
# oarepo-requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""oarepo oaiserver record utils."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invenio_access.permissions import system_identity
from oarepo_runtime import current_runtime

if TYPE_CHECKING:
    from uuid import UUID

    from invenio_records_resources.services.records.results import RecordItem


def get_record(record_uuid: UUID, with_deleted: bool = False) -> RecordItem:
    """Get a record by its UUID."""
    target_pid = current_runtime.find_pid_from_uuid(record_uuid)
    actual_record_service = current_runtime.model_by_pid_type[target_pid.pid_type].service
    return actual_record_service.read(  # type: ignore[no-any-return]
        system_identity, target_pid.pid_value, with_deleted=with_deleted
    )
