#
# Copyright (C) 2025 CESNET z.s.p.o.
#
# oarepo-requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""oarepo oaiserver record utils."""

from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from oarepo_rdm.proxies import current_oarepo_rdm

def get_record(record_uuid, with_deleted=False):
    pids = PersistentIdentifier.query.filter_by(object_uuid=record_uuid).all()
    pids_without_skipped = []
    if not pids:
        raise PIDDoesNotExistError("", record_uuid)
    for pid in pids:
        if pid.pid_type != "oai": # todo - some way to configure skipped pids
            pids_without_skipped.append(pid)
            break
    if not pids_without_skipped:
        raise PIDDoesNotExistError("", record_uuid)
    if len(pids_without_skipped) > 1:
        raise ValueError("Multiple PIDs found")
    target_pid = pids_without_skipped[0]
    actual_record_service = current_oarepo_rdm.record_service_from_pid_type(target_pid.pid_type, is_draft=False)
    return actual_record_service.read(system_identity, target_pid.pid_value)