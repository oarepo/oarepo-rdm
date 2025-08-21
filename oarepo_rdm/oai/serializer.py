#
# Copyright (C) 2025 CESNET z.s.p.o.
#
# oarepo-requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""oarepo oaiserver serializer functions."""

# from oarepo_runtime.resources.responses import OAIExportableResponseHandler
from lxml import etree
from invenio_rdm_records.proxies import current_rdm_records
from invenio_access.permissions import system_identity
from invenio_records_resources.services.records.results import RecordItem
from oarepo_rdm.proxies import current_oarepo_rdm

def get_handler_from_metadata_prefix_and_record_schema(metadata_prefix, record_schema):
    for model in current_oarepo_rdm.rdm_models:
        if model.api_service_config.record_cls.schema.value == record_schema:
            for handler in model.api_resource_config.response_handlers.values():
                pass
#                if isinstance(handler, OAIExportableResponseHandler) and handler.oai_metadata_prefix == metadata_prefix:
#                    return handler
    return None

def oai_serializer(pid, record, **serializer_kwargs):
    record_item = record["_source"]
    if not isinstance(record_item, RecordItem):
        record_item = current_rdm_records.records_service.read(system_identity, record_item['id'])
    serializer = get_handler_from_metadata_prefix_and_record_schema(serializer_kwargs["metadata_prefix"],
                                                                    record_item._record.schema).serializer
    return etree.fromstring(
        serializer.serialize_object(record_item.to_dict()).encode(encoding="utf-8")
    )