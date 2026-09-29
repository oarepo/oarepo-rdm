# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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
