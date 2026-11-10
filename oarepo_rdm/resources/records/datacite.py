# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""DataCite serializers tolerating rights without a title in the default locale."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from datacite import schema43
from flask_resources import BaseListSchema, JSONSerializer, MarshmallowSerializer
from flask_resources.serializers import SimpleSerializer
from invenio_rdm_records.contrib.journal.processors import JournalDataciteDumper
from invenio_rdm_records.resources.serializers.datacite.schema import (
    DataCite43Schema as RDMDataCite43Schema,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


class DataCite43Schema(RDMDataCite43Schema):
    """DataCite 4.3 schema falling back to any language of a rights title.

    Note: this is a temporary patch. The real patch should go to the invenio-rdm-records
    """

    def get_rights(self, obj: Mapping[str, Any]) -> list[Mapping[str, Any]] | None:
        """Get rights, using any available title language.

        Upstream takes only the title in BABEL_DEFAULT_LOCALE; a license titled in another
        language only (e.g. a custom license with just ``en`` on a ``cs`` deployment)
        becomes ``rights: None`` and crashes the DataCite XML builder.
        """
        result = super().get_rights(obj)
        if not result:  # None or marshmallow.missing
            return result
        # the first entries of result map 1:1 to metadata.rights
        for entry, right in zip(cast("list[dict[str, Any]]", result), obj["metadata"].get("rights", []), strict=False):
            if entry.get("rights") is None:
                title = next(iter(right.get("title", {}).values()), None)
                if title:
                    entry["rights"] = title
                else:
                    entry.pop("rights", None)
        return result


class DataCite43JSONSerializer(MarshmallowSerializer):
    """DataCite 4.3 JSON serializer using the patched schema."""

    def __init__(self, is_parent: bool = False, **options: Any) -> None:
        """Construct the serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=DataCite43Schema,
            list_schema_cls=BaseListSchema,
            schema_kwargs={"dumpers": [JournalDataciteDumper()], "is_parent": is_parent},
            **options,
        )


class DataCite43XMLSerializer(MarshmallowSerializer):
    """DataCite 4.3 XML serializer using the patched schema."""

    def __init__(self, **options: Any) -> None:
        """Construct the serializer."""
        super().__init__(
            format_serializer_cls=SimpleSerializer,
            object_schema_cls=DataCite43Schema,
            list_schema_cls=BaseListSchema,
            schema_kwargs={"dumpers": [JournalDataciteDumper()]},
            encoder=options.get("encoder", schema43.tostring),
        )
