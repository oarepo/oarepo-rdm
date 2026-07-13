#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Configuration for RDM overlay."""

from __future__ import annotations

from flask_resources import HTTPJSONException, create_error_handler
from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.services.pids.providers.oai import OAIPIDProvider

from oarepo_rdm.errors import UndefinedModelError

RDM_PERSISTENT_IDENTIFIER_PROVIDERS = [
    OAIPIDProvider(
        "oai",
        label=_("OAI ID"),
    ),
]

RDM_PERSISTENT_IDENTIFIERS = {
    "oai": {
        "providers": ["oai"],
        "required": True,
        "label": _("OAI"),
        "is_enabled": OAIPIDProvider.is_enabled,
    },
}

INFO_ENDPOINT_COMPONENTS = [
    "oarepo_rdm.info:RDMInfoComponent",
]
RDM_RECORDS_ERROR_HANDLERS = {
    UndefinedModelError: create_error_handler(
        lambda exc: HTTPJSONException(
            code=400,
            description=str(exc),
        )
    ),
}
