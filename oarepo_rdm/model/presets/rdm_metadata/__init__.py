#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for RDM metadata."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Literal, cast, override

from deepmerge import always_merger
from oarepo_model import from_yaml
from oarepo_model.api import FunctionalPreset
from oarepo_model.presets.drafts import drafts_preset
from oarepo_model.presets.records_resources import records_resources_preset
from oarepo_model.presets.relations import relations_preset
from oarepo_model.presets.ui import ui_preset
from oarepo_model.presets.ui_links import ui_links_preset

from oarepo_rdm.oai import oai_preset

if TYPE_CHECKING:
    from collections.abc import Mapping

    from oarepo_model.customizations import Customization
    from oarepo_model.model import InvenioModel
    from oarepo_model.presets import Preset


def rdm_model_types() -> dict[str, Any]:
    """Return RDM specific model types."""
    return {
        **from_yaml("rdm.yaml", __file__),
        **from_yaml("rdm_elements.yaml", __file__),
    }


class RDMMetadataPreset(FunctionalPreset):
    """Preset for RDM metadata."""

    kind: Literal["minimal", "basic", "complete"]
    metadata_types: Mapping[str, str] = {
        "minimal": "RDMMinimalMetadata",
        "basic": "RDMBasicMetadata",
        "complete": "RDMCompleteMetadata",
    }

    @override
    def before_invenio_model(self, params: dict[str, Any]) -> None:
        """Perform extra action before the Invenio model is created."""
        if "metadata_type" not in params:
            params["metadata_type"] = self.metadata_types[self.kind]

        # add required presets
        extra_presets = [
            records_resources_preset,
            drafts_preset,
            oai_preset,
            ui_preset,
            ui_links_preset,
            relations_preset,
        ]
        params["presets"][:0] = extra_presets

    @override
    def before_populate_type_registry(
        self,
        model: InvenioModel,
        types: list[dict[str, Any]],
        presets: list[type[Preset] | list[type[Preset]] | tuple[type[Preset]]],
        customizations: list[Customization],
        params: dict[str, Any],
    ) -> None:
        """Perform extra action before populating the type registry."""
        types.append(rdm_model_types())
        metadata_type = params["metadata_type"]
        merge_metadata(types, metadata_type, self.metadata_types[self.kind])


def merge_metadata(types: list[dict[str, Any]], metadata_type: str, rdm_type: str) -> None:
    """Merge metadata from one type to another.

    :param types: The list of types to modify.
    :param from_type: The type to merge from.
    :param to_type: The type to merge to.
    """
    if metadata_type == rdm_type:
        # already the same, just return
        return

    def select_type(type_name: str, copy_value: bool = False) -> dict[str, Any] | None:
        for type_dict in types:
            if type_name not in type_dict:
                continue
            tested_type_def = type_dict[type_name]
            if copy_value:
                copied = copy.copy(tested_type_def)
                type_dict[type_name] = copied
                return cast("dict[str, Any]", copied)
            return cast("dict[str, Any]", tested_type_def)
        raise ValueError(f"Type {type_name} not found")

    from_metadata = select_type(metadata_type, copy_value=True)
    from_rdm = select_type(rdm_type)

    always_merger.merge(from_metadata, from_rdm)
