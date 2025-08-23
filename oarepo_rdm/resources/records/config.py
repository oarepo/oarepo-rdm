#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""UI serializer for RDM records."""

from __future__ import annotations

from invenio_rdm_records.resources.config import RDMRecordResourceConfig


class OARepoRDMRecordResourceConfig(RDMRecordResourceConfig):
    routes = {
        **RDMRecordResourceConfig.routes,
        "all-prefix": "/all",  # /api/all/records
    }


# def global_search_response_handlers():
#     """Return UI global search handlers."""
#     serializers: list[dict] = [
#         {
#             "schema": model.api_service.record_cls.schema.value,
#             "serializer": model.api_resource.config.response_handlers[
#                 "application/vnd.inveniordm.v1+json"
#             ].serializer,
#         }
#         for model in current_oarepo_rdm.rdm_models
#     ]

#     return GlobalSearchResponseHandler(serializers)
