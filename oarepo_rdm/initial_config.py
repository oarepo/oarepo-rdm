#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Initial configuration which replaces RDM service with oarepo extensions."""

from __future__ import annotations

from datetime import datetime

from flask_resources import HTTPJSONException, create_error_handler
from invenio_rdm_records.resources.config import error_handlers

from oarepo_rdm.errors import UndefinedModelError
from oarepo_rdm.oai.config import OAIServerMetadataFormats

RDM_RECORDS_SERVICE_CONFIG_CLASS = "oarepo_rdm.services.config:OARepoRDMServiceConfig"
"""Service config class."""

RDM_RECORDS_SERVICE_CLASS = "oarepo_rdm.services.service:OARepoRDMService"
"""Replacement for the plain RDM service class."""

RDM_RECORDS_RESOURCE_CONFIG_CLASS = "oarepo_rdm.resources.records.config:OARepoRDMRecordResourceConfig"
"""Resource config class."""

RDM_RECORDS_RESOURCE_CLASS = "oarepo_rdm.resources.records.resource:OARepoRDMRecordResource"
"""Replacement for the plain RDM resource class."""

RDM_RECORDS_COMMUNITY_RECORDS_CONFIG_CLASS = "oarepo_rdm.services.config:OARepoCommunityRecordsConfig"
"""Community records service config that uses the multiplexed search options."""

RDM_RECORDS_COMMUNITY_RECORDS_SERVICE_CLASS = "oarepo_rdm.services.service:OARepoCommunityRecordsService"
"""Community records service that multiplexes search across per-model services."""

RDM_RECORDS_REVIEW_SERVICE_CLASS = "oarepo_rdm.services.delegating.DelegatingReviewService"
RDM_RECORDS_ACCESS_SERVICE_CLASS = "oarepo_rdm.services.delegating.DelegatingRecordAccessService"
RDM_RECORDS_PIDS_SERVICE_CLASS = "oarepo_rdm.services.delegating.DelegatingPIDsService"

# OAI-PMH
# =======
# See https://github.com/inveniosoftware/invenio-oaiserver/blob/master/invenio_oaiserver/config.py
# (Using GitHub because documentation site out-of-sync at time of writing)


OAISERVER_METADATA_FORMATS = OAIServerMetadataFormats()


RDM_RECORDS_ERROR_HANDLERS = {
    **error_handlers,
    UndefinedModelError: create_error_handler(
        lambda exc: HTTPJSONException(
            code=400,
            description=str(exc),
        )
    ),
}
APP_RDM_RECORD_LANDING_PAGE_TEMPLATE = "oarepo_rdm/record_detail_iframe.html"

APP_RDM_DEPOSIT_FORM_DEFAULTS = {
    "publication_date": lambda: datetime.now().strftime("%Y-%m-%d"),  # noqa: DTZ005
}
"""Default values pre-filled in the deposit form for new records."""
