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

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services.schemas.metadata import MetadataSchema as RDMMetadataSchema
from oarepo_model.customizations import Customization, PrependMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMRecordMetadataSchemaPreset(Preset):
    """Preset for RDM record with files schema class."""

    modifies = ("MetadataSchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield PrependMixin("MetadataSchema", RDMMetadataSchema)
