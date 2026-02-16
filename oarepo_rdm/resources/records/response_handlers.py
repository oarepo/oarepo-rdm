#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Response handlers for RDM records."""

from __future__ import annotations

import copy
from collections import defaultdict
from typing import TYPE_CHECKING, Any, cast, override

from flask_resources import MarshmallowSerializer, ResponseHandler
from flask_resources.serializers.base import BaseSerializer
from invenio_records_resources.resources.records.headers import etag_headers
from marshmallow import Schema
from oarepo_runtime import current_runtime
from werkzeug.exceptions import NotAcceptable

if TYPE_CHECKING:
    from collections.abc import Mapping


def get_response_handlers() -> Mapping[str, ResponseHandler]:
    """Get possible response handlers for all registered RDM models."""
    mimetypes = defaultdict[str, list[BaseSerializer]](list)
    for model in current_runtime.rdm_models:
        for export in model.exports:
            mimetypes[export.mimetype].append(export.serializer)
    return {
        mimetype: ResponseHandler(DelegatedSerializer(mimetype, serializers), headers=etag_headers)
        for mimetype, serializers in mimetypes.items()
    }


class NoOpSchema(Schema):
    """A no-operation dump-only schema that returns data as is."""

    @override
    def dump(self, obj: Any, *, many: bool | None = None) -> Any:
        """Return the object as is."""
        return obj


class DelegatedSerializer(BaseSerializer):
    """Response handler that delegates to the correct model's handler."""

    def __init__(self, mimetype: str, serializers: list[BaseSerializer]) -> None:
        """Initialize the delegated response handler."""
        self.mimetype = mimetype
        self.serializers = serializers

    def serialize_object(self, obj: Any) -> Any:
        """Serialize a single object according to the response ctx."""
        exporter = self._get_exporter(obj)
        if exporter is None:
            raise NotAcceptable(
                f"No export found for schema {obj.get('$schema', None)}, "
                f"record id {obj.get('id', None)} and mimetype {self.mimetype}."
            )
        return exporter.serialize_object(obj)

    def _extract_hits(self, obj: Any) -> list[Any]:
        """Extract hits from the given object."""
        # note: this is hardcoded to opensearch results structure, we can not generalize it
        # as we do not know which serializers could match and can not use those
        return cast("list", obj.get("hits", {}).get("hits", []))

    def _update_hits(self, original: Any, updated_hits: list[Any]) -> Any:
        """Update the hits in the original object with the updated hits."""
        # duplicate original to not modify in place. For performance reasons we use
        # shallow copy of the whole structure except hits.hits which we replace
        updated = {**original}
        updated["hits"] = {**updated.get("hits", {})}
        updated["hits"]["hits"] = updated_hits
        return updated

    def serialize_object_list(self, obj_list: dict) -> Any:
        """Serialize a list of objects according to the response ctx.

        The supported obj_list is either a plain list (unlikely) or a result of opensearch query.
        """
        obj_list_data = self._extract_hits(obj_list)

        # 1. get exporters for all objects
        possible_exporters = [(obj, self._get_exporter(obj)) for obj in obj_list_data]
        exporters = [(obj, exporter) for obj, exporter in possible_exporters if exporter is not None]

        # 2. if no exporters found, return empty list serialization
        if not exporters:
            return self.serializers[0].serialize_object_list(self._update_hits(obj_list, []))

        # 3. if all exporters are the same, use it
        if all(type(exporter[1]) is type(exporters[0][1]) for exporter in exporters):
            return exporters[0][1].serialize_object_list(self._update_hits(obj_list, [x[0] for x in exporters]))

        # 4. if not, check if all exporters are instance of MarshmallowSerializer
        if not all(isinstance(exporter[1], MarshmallowSerializer) for exporter in exporters):
            raise NotAcceptable(  # pragma: no cover
                "Cannot serialize list with multiple different non-marshmallow serializers."
            )

        # TODO: will need to be changed when Christoph's changes are merged
        serialized_objects = [
            cast("MarshmallowSerializer", exporter[1]).dump_obj(exporter[0]) for exporter in exporters
        ]

        serializer = cast("MarshmallowSerializer", copy.copy(exporters[0][1]))
        if serializer.list_schema:
            new_list_schema = type(serializer.list_schema)(
                context={
                    **serializer.list_schema.context,
                    "object_schema_cls": NoOpSchema,
                }
            )
            serializer.list_schema = new_list_schema
        else:
            raise NotImplementedError(  # pragma: no cover
                "Cannot serialize list without list schema in mixed marshmallow serializers."
            )
        return serializer.serialize_object_list(self._update_hits(obj_list, serialized_objects))

    def _get_exporter(self, obj: Any) -> BaseSerializer | None:
        """Get the exporter for the given object."""
        schema = obj.get("$schema", None)
        if not schema:
            raise ValueError("Object does not have $schema defined.")  # pragma: no cover
        rdm_model = current_runtime.rdm_models_by_schema[schema]
        for export in rdm_model.exports:
            if export.mimetype == self.mimetype:
                return export.serializer
        return None
