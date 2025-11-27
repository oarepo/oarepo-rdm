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

from typing import Any

from flask import current_app
from invenio_app_rdm import config as rdm_config  # noqa
from werkzeug.local import LocalProxy

from oarepo_rdm.oai.config import OAIServerMetadataFormats

# TODO: Why not to add other RDM routes here?
APP_RDM_ROUTES = {
    "index": "/",
    "robots": "/robots.txt",
    "help_search": "/help/search",
    "help_statistics": "/help/statistics",
    # "help_versioning": "/help/versioning", #noqa
    "record_search": "/search",
    "record_detail": "/records/<pid_value>",
    "record_export": "/records/<pid_value>/export/<export_format>",
    "record_file_preview": "/records/<pid_value>/preview/<path:filename>",
    "record_file_download": "/records/<pid_value>/files/<path:filename>",
    "record_thumbnail": "/records/<pid_value>/thumb<int:size>",
    "record_media_file_download": "/records/<pid_value>/media-files/<path:filename>",
    "record_from_pid": "/<any({schemes}):pid_scheme>/<path:pid_value>",
    "record_latest": "/records/<pid_value>/latest",
    # "dashboard_home": "/me", #noqa
    # "deposit_create": "/uploads/new", #noqa
    # "deposit_edit": "/uploads/<pid_value>", #noqa
}


RDM_RECORDS_SERVICE_CONFIG_CLASS = "oarepo_rdm.services.config:OARepoRDMServiceConfig"
"""Service config class."""

RDM_RECORDS_SERVICE_CLASS = "oarepo_rdm.services.service:OARepoRDMService"
"""Replacement for the plain RDM service class."""

RDM_RECORDS_RESOURCE_CONFIG_CLASS = "oarepo_rdm.resources.records.config:OARepoRDMRecordResourceConfig"
"""Resource config class."""

RDM_RECORDS_RESOURCE_CLASS = "oarepo_rdm.resources.records.resource:OARepoRDMRecordResource"
"""Replacement for the plain RDM resource class."""


# OAI-PMH
# =======
# See https://github.com/inveniosoftware/invenio-oaiserver/blob/master/invenio_oaiserver/config.py
# (Using GitHub because documentation site out-of-sync at time of writing)


def _site_name(site_url: str) -> str:
    """Get the site name from the URL."""
    # get just the host from the url
    return site_url.split("//")[-1].split("/")[0]


OAISERVER_ID_PREFIX = LocalProxy(lambda: _site_name(current_app.config["SITE_UI_URL"]))
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

OAISERVER_RECORD_SETS_FETCHER = "invenio_oaiserver.percolator:find_sets_for_record"
"""Record's OAI sets function."""

OAISERVER_RECORD_INDEX = "oaisource"
"""oaisource is a mapping alias for records that can be sent over OAI-PMH.

To mark your model as oaisource, add `oarepo_rdm.oai.oai_presets` to your model's presets."""

# TODO: oarepo extension, maybe not needed
OAISERVER_RECORD_LIST_SETS_FETCHER = "invenio_oaiserver.percolator:sets_search_all"

"""Specify a search index with records that should be exposed via OAI-PMH."""

OAISERVER_GETRECORD_FETCHER = "invenio_rdm_records.oai:getrecord_fetcher"
"""Record data fetcher for serialization."""

# extra oarepo extensions - TODO: maybe not needed
OAISERVER_NEW_PERCOLATOR_FUNCTION = "invenio_oaiserver.percolator:_new_percolator"
# TODO: maybe not needed
OAISERVER_DELETE_PERCOLATOR_FUNCTION = "invenio_oaiserver.percolator:_delete_percolator"

# cleared rest endpoints
RECORDS_REST_ENDPOINTS: list[Any] = []

APP_RDM_USER_DASHBOARD_ROUTES = {
    "uploads": "/me/uploads",
    "communities": "/me/communities",
    "requests": "/me/requests",
}
"""Routes for user dashboard"""

USER_DASHBOARD_MENU_OVERRIDES: dict[str, str] = {}
"""Menu overrides for user dashboard"""

RDM_SEARCH_USER_COMMUNITIES = {
    "facets": ["visibility", "type"],
    "sort": ["bestmatch", "newest", "oldest"],
}
"""User communities search configuration"""

RDM_SEARCH_USER_REQUESTS = {
    "facets": ["type", "status"],
    "sort": ["bestmatch", "newest", "oldest"],
}
"""User requests search configuration"""


RDM_COMMUNITIES_ROUTES = {
    "community-detail": "/communities/<pid_value>/records",
    "community-home": "/communities/<pid_value>/",
    "community-browse": "/communities/<pid_value>/browse",
    "community-static-page": "/communities/<pid_value>/pages/<path:page_slug>",
    "community-collection": "/communities/<pid_value>/collections/<tree_slug>/<collection_slug>",
}
"""Communities routes from app RDM."""


COMMUNITIES_RECORDS_SEARCH = {
    "facets": ["access_status", "resource_type", "language"],
    "sort": ["bestmatch", "newest", "oldest", "version"],
}
"""Communities records search configuration."""
