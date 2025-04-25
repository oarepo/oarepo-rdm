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
    if not pids:
        raise PIDDoesNotExistError("", record_uuid)
    if len(pids) > 2:
        raise ValueError("Multiple PIDs found") # todo - this should be configurable
    for pid in pids:
        if pid.pid_type != "oai":
            target_pid = pid
            break
    actual_record_service = current_oarepo_rdm.record_service_from_pid_type(target_pid.pid_type, is_draft=False)
    return actual_record_service.read(system_identity, target_pid.pid_value)

    #actual_record_cls = current_oarepo_rdm.record_cls_from_pid_type(target_pid.pid_type, is_draft=False)
    #return actual_record_cls.get_record(record_uuid)

def getrecord_fetcher(record_uuid):
    """Fetch record data as dict with identity check for serialization."""
    record = get_record(record_uuid)

    dumper = record._record.dumper

    #record = dumper.dump(record._record, record.data)  # todo this did not work in the percolator index

    record_new = dumper.dump(record._record, record.data)
    record = record._record.dumps()
    diff1 = set(record_new.keys()) - set(record.keys())
    diff2 = set(record.keys()) - set(record_new.keys())

    return record