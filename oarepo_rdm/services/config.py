#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Configuration of the RDM service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

import marshmallow as ma
from invenio_drafts_resources.services.records.config import (
    SearchOptions,
    is_record,
)
from invenio_rdm_records.services.config import RDMRecordServiceConfig
from invenio_records_resources.services.base.links import (
    ConditionalLink,
    LinksTemplate,
)
from invenio_records_resources.services.records.links import (
    RecordEndpointLink,
)
from marshmallow import types
from oarepo_runtime import current_runtime

from oarepo_rdm.proxies import current_oarepo_rdm

from .results import MultiplexingResultList

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from flask_principal import Identity
    from invenio_records_resources.services.records.config import (
        SearchOptions,
    )


class MultiplexingLinks(LinksTemplate):
    """Multiplexing links for the RDM service.

    Based on the record being serialized, the expansion is delegated
    to the appropriate service.
    """

    @override
    def expand(self, identity: Identity, obj: Any, **kwargs: Any) -> dict[str, str]:
        """Expand links for the given record."""
        if obj is None:
            return {}

        schema = obj["$schema"]
        delegated_model = current_runtime.rdm_models_by_schema[schema]
        delegated_service = delegated_model.service
        return cast(
            "dict[str, str]",
            # TODO: seems to be correct but what to do with kwargs?
            delegated_service.links_item_tpl.expand(identity, obj),
        )


class MultiplexingSchema(ma.Schema):
    """Multiplexing schema for the RDM service.

    Based on the record being (de)serialized, the schema loading and dumping
    is delegated to the appropriate service.
    """

    @override
    def load(
        self,
        data: Mapping[str, Any] | Iterable[Mapping[str, Any]],
        *,
        many: bool | None = None,
        partial: bool | types.StrSequenceOrSet | None = None,  # type: ignore[assignment]
        unknown: str | None = None,
    ) -> Any:
        if many:
            return [self.load(item, many=False, partial=partial, unknown=unknown) for item in data]  # type: ignore[union-attr, arg-type]
        schema = cast("Mapping[str, Any]", data)["$schema"]
        delegated_model = current_runtime.rdm_models_by_schema[schema]
        delegated_service = delegated_model.service
        return delegated_service.schema.load(
            data,  # type: ignore[arg-type]
            schema_args={},  # type: ignore[arg-type]
            context=self.context,
            raise_errors=True,
        )

    @override
    def dump(self, obj: Any, *, many: bool | None = None) -> Any:
        if many:
            return [self.dump(item, many=False) for item in obj]  # type: ignore[union-attr]
        schema = cast("Mapping[str, Any]", obj)["$schema"]
        delegated_model = current_runtime.rdm_models_by_schema[schema]
        delegated_service = delegated_model.service
        return delegated_service.schema.dump(obj, schema_args={}, context={**self.context, "record": obj})  # type: ignore[arg-type]


class OARepoRDMServiceConfig(RDMRecordServiceConfig):
    """OARepo extension to RDM record service configuration."""

    result_list_cls = MultiplexingResultList
    schema = MultiplexingSchema  # type: ignore[assignment]

    # TODO: add proper links here, not just this subset
    links_item: Mapping[str, Any] = {
        # Record
        "self": ConditionalLink(
            cond=is_record,
            if_=RecordEndpointLink("records.read"),
            else_=RecordEndpointLink("records.read_draft"),
        ),
        "self_html": ConditionalLink(
            cond=is_record,
            if_=RecordEndpointLink("invenio_app_rdm_records.record_detail"),
            else_=RecordEndpointLink("invenio_app_rdm_records.deposit_edit"),
        ),
    }

    @property
    @override
    def search(self) -> SearchOptions:  # type: ignore[override]
        return current_oarepo_rdm.search_options

    @search.setter
    def search(self, _value: Any) -> None:  # type: ignore[override]
        raise AttributeError("search is read-only")  # pragma: no cover

    @property
    @override
    def search_drafts(self) -> SearchOptions:  # type: ignore[override]
        return current_oarepo_rdm.draft_search_options

    @search_drafts.setter
    def search_drafts(self, _value: Any) -> None:  # type: ignore[override]
        raise AttributeError("search_drafts is read-only")  # pragma: no cover

    @property
    @override
    def search_versions(self) -> SearchOptions:  # type: ignore[override]
        return current_oarepo_rdm.versions_search_options

    @search_versions.setter
    def search_versions(self, _value: Any) -> None:  # type: ignore[override]
        raise AttributeError("search_versions is read-only")  # pragma: no cover

    @property
    def search_all(self) -> SearchOptions:
        """Return search options for searching all records (published and everyone's drafts)."""
        return current_oarepo_rdm.all_search_options

    @search_all.setter
    def search_all(self, _value: Any) -> None:
        raise AttributeError("search_all is read-only")  # pragma: no cover
