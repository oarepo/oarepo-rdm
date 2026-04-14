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

from invenio_drafts_resources.services.records.config import (
    is_draft,
)
from invenio_rdm_records.services.config import (
    RDMRecordServiceConfig,
    ThumbnailLinks,
    _groups_enabled,
    archive_download_enabled,
    has_image_files,
    is_draft_and_has_review,
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
from oarepo_model.api import FunctionalPreset
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
    from types import SimpleNamespace

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
                "reserve_doi": RecordEndpointLink(
                    "records.pids_reserve",
                    params=["pid_value", "scheme"],
                    vars=lambda record, parameters: parameters.update({"scheme": "doi"}),  # noqa: ARG005
                ),
                "files": ConditionalLink(
                    cond=is_published_record(),
                    if_=RecordEndpointLink(f"{model.blueprint_base}_files.search"),
                    else_=RecordEndpointLink(f"{model.blueprint_base}_draft_files.search"),
                ),
                "submit-review": RecordEndpointLink(
                    "records.review_submit",
                    when=is_draft_and_has_review,
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
                "review": RecordEndpointLink("records.review_read", when=is_draft),
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


class RDMCheckLinksDefinedPreset(FunctionalPreset):
    """Preset for checking all RDM item links are present in the model."""

    @override
    def after_model_built(
        self,
        model: InvenioModel,
        types: list[dict[str, Any]],
        presets: list[type[Preset] | list[type[Preset]] | tuple[type[Preset]]],
        builder: InvenioModelBuilder,
        customizations: list[Customization],
        model_namespace: SimpleNamespace,
        params: dict[str, Any],
    ) -> None:

        rdm_links = set(RDMRecordServiceConfig.links_item.keys())
        model_links = set(model_namespace.RecordServiceConfig().links_item.keys())

        if not rdm_links <= model_links:
            raise ValueError(f"RDM complete model {model.name} links miss RDM links links: {rdm_links - model_links}")
