# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate RDM record schema mixin with files metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services.records.schema import RecordSchema as BaseRecordSchema
from invenio_rdm_records.services.schemas.record import (
    RDMRecordSchema,
)
from oarepo_model.customizations import Customization, ReplaceBaseClass
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


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
        yield ReplaceBaseClass("RecordSchema", BaseRecordSchema, RDMRecordSchema)
