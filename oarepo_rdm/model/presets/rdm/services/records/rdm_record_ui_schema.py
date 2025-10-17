#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""UI JSON serializer preset for Invenio record resources.

This module provides a preset that creates a JSON serializer specifically designed
for user interface contexts. It includes:

- JSONUISerializerPreset: A preset that provides the JSONUISerializer class
- JSONUISerializer: A Marshmallow-based serializer that uses the RecordUISchema
  for object serialization and outputs JSON format with UI-specific context
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import AddMixins, Customization
from oarepo_model.presets import Preset

from oarepo_rdm.services.schemas import ui_serialized_record

if TYPE_CHECKING:
    from collections.abc import Generator

    from marshmallow import Schema as BaseSchema
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel
else:
    BaseSchema = object


class RDMRecordUISchemaPreset(Preset):
    """Preset which modifies the RecordUISchema to remember the serialized record."""

    modifies = ("RecordUISchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RDMUISchemaMixin(BaseSchema):
            @override
            def dump(self, obj: Any, *, many: bool | None = None) -> Any:
                many = self.many if many is None else bool(many)
                if many:
                    raise NotImplementedError(  # pragma: no cover
                        "ui_serialized_record contextvar not implemented for many=True"
                    )
                token = ui_serialized_record.set(obj)
                try:
                    return super().dump(obj, many=many)
                finally:
                    ui_serialized_record.reset(token)

        yield AddMixins("RecordUISchema", RDMUISchemaMixin)
