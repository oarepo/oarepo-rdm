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
    ThumbnailLinks,
    _groups_enabled,
    archive_download_enabled,
    has_image_files,
    record_thumbnail_sizes,
    vars_self_iiif,
)
from invenio_records_resources.services.base.links import (
    ConditionalLink,
    EndpointLink,
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
from werkzeug.local import LocalProxy

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
                # TODO: add parent_doi, doi, self_doi to be compatible with rdm
                "self_iiif_manifest": EndpointLink("iiif.manifest", params=["uuid"], vars=vars_self_iiif),
                "self_iiif_sequence": EndpointLink("iiif.sequence", params=["uuid"], vars=vars_self_iiif),
                # Files
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
                "thumbnails": ThumbnailLinks(
                    sizes=LocalProxy(record_thumbnail_sizes),  # type: ignore[assignment]
                    when=has_image_files,
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
                # Access
                "access_links": RecordEndpointLink("record_links.search"),
                "access_grants": RecordEndpointLink("record_grants.search"),
                "access_users": RecordEndpointLink("record_user_access.search"),
                "access_groups": RecordEndpointLink(
                    "record_group_access.search",
                    when=_groups_enabled,
                ),
                # Working out of the box
                "access_request": RecordEndpointLink("records.create_access_request"),
                "access": RecordEndpointLink("records.update_access_settings"),
            },
        )

        # Versions
        yield AddToDictionary(
            "record_version_search_links",
            rdm_pagination_record_endpoint_links(f"{model.blueprint_base}.search_versions"),
        )
