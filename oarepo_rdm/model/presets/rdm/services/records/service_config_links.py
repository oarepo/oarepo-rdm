#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring RDM service config links."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services.config import (
    RDMRecordServiceConfig,
    archive_download_enabled,
)
from invenio_records_resources.services.base.links import (
    ConditionalLink,
)
from invenio_records_resources.services.records.links import (
    RecordEndpointLink,
)
from oarepo_model.customizations import (
    AddToDictionary,
    Customization,
)
from oarepo_model.presets import Preset
from oarepo_runtime.services.config import (
    is_published_record,
)
from oarepo_runtime.services.records.links import rdm_pagination_record_endpoint_links

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMServiceConfigLinks(Preset):
    """Preset for extra RDM service config links."""

    modifies = ("record_links_item", "record_version_search_links")

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddToDictionary(
            "record_links_item",
            {
                **RDMRecordServiceConfig.links_item,
                "files": ConditionalLink(
                    cond=is_published_record(),
                    if_=RecordEndpointLink(f"{model.blueprint_base}_files.search"),
                    else_=RecordEndpointLink(f"{model.blueprint_base}_draft_files.search"),
                ),
                "media_files": ConditionalLink(
                    cond=is_published_record(),
                    if_=RecordEndpointLink(f"{model.blueprint_base}_media_files.search"),
                    else_=RecordEndpointLink(f"{model.blueprint_base}_draft_media_files.search"),
                ),
                # Reads a zipped version of all files
                "archive": ConditionalLink(
                    cond=is_published_record(),
                    if_=RecordEndpointLink(
                        f"{model.blueprint_base}_files.read_archive",
                        when=archive_download_enabled,
                    ),
                    else_=RecordEndpointLink(
                        f"{model.blueprint_base}_draft_files.read_archive",
                        when=archive_download_enabled,
                    ),
                ),
                "archive_media": ConditionalLink(
                    cond=is_published_record(),
                    if_=RecordEndpointLink(
                        f"{model.blueprint_base}_media_files.read_archive",
                        when=archive_download_enabled,
                    ),
                    else_=RecordEndpointLink(
                        f"{model.blueprint_base}_draft_media_files.read_archive",
                        when=archive_download_enabled,
                    ),
                ),
            },
            override_values=False,
        )
        # Versions
        yield AddToDictionary(
            "record_version_search_links",
            rdm_pagination_record_endpoint_links(f"{model.blueprint_base}.search_versions"),
        )
