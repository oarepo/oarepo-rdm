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

from typing import TYPE_CHECKING

from invenio_rdm_records.resources.config import RDMRecordResourceConfig
from proxytypes import LazyProxy

from .response_handlers import get_response_handlers

if TYPE_CHECKING:
    from collections.abc import Mapping

    from invenio_rdm_records.resources.config import RDMRecordResourceConfig as RDMRecordResourceConfig_Typing
else:
    RDMRecordResourceConfig_Typing = object


class OARepoRDMRecordResourceConfigMixin(RDMRecordResourceConfig_Typing):
    """Mixin for RDM record resource configuration."""

    @property
    def routes(self) -> Mapping[str, str]:  # type: ignore[reportIncompatibleVariableOverride]
        """Override routes to use path instead of default converter for pid_value.

        This was causing a problem when PID contained slashes (doi:1234/zenodo.12345 for example).
        It would parse only first part before the slash.
        Also adds /all prefix to routes.
        """
        routes = {k: v.replace("<pid_value>", "<path:pid_value>") for k, v in super().routes.items()}
        routes["all-prefix"] = "/all"  # /api/all/records
        return routes


class OARepoRDMRecordResourceConfig(OARepoRDMRecordResourceConfigMixin, RDMRecordResourceConfig):  # type: ignore[reportIncompatibleVariableOverride]
    """OARepo extension to RDM record resource configuration."""

    response_handlers = LazyProxy(get_response_handlers)  # type: ignore[reportAssignmentType]
