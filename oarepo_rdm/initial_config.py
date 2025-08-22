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

from flask import current_app
from invenio_app_rdm import config as rdm_config  # noqa
from invenio_rdm_records.proxies import current_rdm_records_service
from werkzeug.local import LocalProxy

from oarepo_rdm.oai.config import OAIServerMetadataFormats

# TODO: why is this needed? Why not to add other RDM routes here?
APP_RDM_ROUTES = (
    {
        "record_detail": "/records/<pid_value>",
        "record_file_download": "/records/<pid_value>/files/<path:filename>",
    },
)

RDM_RECORDS_SERVICE_CONFIG_CLASS = "oarepo_rdm.services.config:OARepoRDMServiceConfig"
"""Service config class."""

RDM_RECORDS_SERVICE_CLASS = "oarepo_rdm.services.service:OARepoRDMService"
"""Replacement for the plain RDM service class."""


# OAI-PMH
# =======
# See https://github.com/inveniosoftware/invenio-oaiserver/blob/master/invenio_oaiserver/config.py
# (Using GitHub because documentation site out-of-sync at time of writing)


def _site_name(site_url: str) -> str:
    """Get the site name from the URL."""
    # get just the host from the url
    return site_url.split("//")[-1].split("/")[0]


OAISERVER_ID_PREFIX = LocalProxy(lambda: f"oai:{_site_name(current_app.config['SITE_UI_URL'])}:")
"""The prefix that will be applied to the generated OAI-PMH ids."""

OAISERVER_SEARCH_CLS = "invenio_rdm_records.oai:OAIRecordSearch"
"""Class for record search."""

OAISERVER_ID_FETCHER = "invenio_rdm_records.oai:oaiid_fetcher"
"""OAI ID fetcher function."""

OAISERVER_METADATA_FORMATS = OAIServerMetadataFormats()

OAISERVER_LAST_UPDATE_KEY = "updated"
"""Record update key."""

OAISERVER_CREATED_KEY = "created"
"""Record created key."""

OAISERVER_RECORD_CLS = "invenio_rdm_records.records.api:RDMRecord"
"""Record retrieval class."""

OAISERVER_RECORD_SETS_FETCHER = "oarepo_rdm.oai.percolator:find_sets_for_record"
"""Record's OAI sets function."""

OAISERVER_RECORD_INDEX = LocalProxy(
    lambda: current_rdm_records_service.record_cls.index._name  # noqa: SLF001 # type: ignore[attr-defined]
)
OAISERVER_RECORD_LIST_SETS_FETCHER = "oarepo_rdm.oai.percolator:sets_search_all"

"""Specify a search index with records that should be exposed via OAI-PMH."""

OAISERVER_GETRECORD_FETCHER = "oarepo_rdm.oai.record:get_record"
"""Record data fetcher for serialization."""

# extra oarepo extensions
OAISERVER_NEW_PERCOLATOR_FUNCTION = "oarepo_rdm.oai.percolator:_new_percolator"
OAISERVER_DELETE_PERCOLATOR_FUNCTION = "oarepo_rdm.oai.percolator:_delete_percolator"
