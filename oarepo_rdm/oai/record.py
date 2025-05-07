#
# Copyright (C) 2025 CESNET z.s.p.o.
#
# oarepo-requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""oarepo oaiserver record utils."""

from invenio_access.permissions import system_identity
from oarepo_runtime.datastreams.utils import get_record_service_for_record_class

from oarepo_rdm.proxies import current_oarepo_rdm

def get_record(record_uuid, with_deleted=False):
    target_pid = current_oarepo_rdm.pid_from_uuid(record_uuid)
    record_cls = current_oarepo_rdm.record_cls_from_pid_type(target_pid.pid_type, is_draft=False)
    actual_record_service = get_record_service_for_record_class(record_cls)
    return actual_record_service.read(system_identity, target_pid.pid_value)