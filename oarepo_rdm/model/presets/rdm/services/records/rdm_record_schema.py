#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see http://github.com/oarepo/oarepo-rdm).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate RDM record schema mixin with files metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, override

from invenio_rdm_records.services.schemas.access import AccessSchema
from invenio_rdm_records.services.schemas.files import FilesSchema
from invenio_rdm_records.services.schemas.pids import PIDSchema
from invenio_rdm_records.services.schemas.record import (
    InternalNoteSchema,
    validate_scheme,
)
from invenio_rdm_records.services.schemas.stats import StatsSchema
from invenio_rdm_records.services.schemas.tombstone import (
    DeletionStatusSchema,
    TombstoneSchema,
)
from invenio_rdm_records.services.schemas.versions import VersionsSchema
from marshmallow import EXCLUDE, fields, post_dump
from marshmallow_utils.fields import (
    NestedAttribute,
    SanitizedUnicode,
)
from marshmallow_utils.permissions import FieldPermissionsMixin
from oarepo_model.customizations import Customization, PrependMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMRecordSchemaMixin(FieldPermissionsMixin):
    """Record schema."""

    class Meta:
        """Meta attributes for the schema."""

        unknown = EXCLUDE

    # ATTENTION: In this schema you should be using the ``NestedAttribute``
    # instead  of Marshmallow's ``fields.Nested``. Using NestedAttribute
    # ensures that the nested schema will receive the system field instead of
    # the record dict (i.e. record.myattr instead of record['myattr']).

    pids = fields.Dict(
        keys=SanitizedUnicode(validate=validate_scheme),
        values=fields.Nested(PIDSchema),
    )

    # provenance
    access = NestedAttribute(AccessSchema)
    files = NestedAttribute(FilesSchema)
    media_files = NestedAttribute(FilesSchema)
    revision = fields.Integer(dump_only=True)
    versions = NestedAttribute(VersionsSchema, dump_only=True)
    is_published = fields.Boolean(dump_only=True)
    status = fields.String(dump_only=True)
    tombstone = fields.Nested(TombstoneSchema, dump_only=True)
    deletion_status = fields.Nested(DeletionStatusSchema, dump_only=True)
    internal_notes = fields.List(fields.Nested(InternalNoteSchema))
    stats = NestedAttribute(StatsSchema, dump_only=True)
    # schema_version = fields.Integer(dump_only=True) # noqa

    field_dump_permissions: ClassVar[dict[str, str]] = {
        "internal_notes": "manage_internal",
    }

    field_load_permissions: ClassVar[dict[str, str]] = {
        "internal_notes": "manage_internal",
    }

    def default_nested(self, data: dict[str, Any]) -> dict[str, Any]:
        """Serialize fields as empty dict for partial drafts.

        Cannot use marshmallow for Nested fields due to issue:
        https://github.com/marshmallow-code/marshmallow/issues/1566
        https://github.com/marshmallow-code/marshmallow/issues/41
        and more.
        """
        if not data.get("metadata"):
            data["metadata"] = {}
        if not data.get("pids"):
            data["pids"] = {}
        if not data.get("custom_fields"):
            data["custom_fields"] = {}
        return data

    def hide_tombstone(self, data: dict[str, Any]) -> dict[str, Any]:
        """Hide tombstone info if the record isn't deleted and metadata if it is."""
        is_deleted = (data.get("deletion_status") or {}).get("is_deleted", False)
        tombstone_visible = (data.get("tombstone") or {}).get("is_visible", True)

        if not is_deleted or not tombstone_visible:
            data.pop("tombstone", None)

        return data

    @post_dump
    def post_dump(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:  # noqa: ARG002
        """Perform some updates on the dumped data."""
        data = self.default_nested(data)
        return self.hide_tombstone(data)


class RDMRecordSchemaPreset(Preset):
    """Preset for RDM record with files schema class."""

    modifies = ("RecordSchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield PrependMixin("RecordSchema", RDMRecordSchemaMixin)
