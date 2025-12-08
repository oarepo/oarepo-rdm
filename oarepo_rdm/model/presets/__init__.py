#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""RDM model presets for oarepo-model package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .rdm import rdm_static_preset
from .rdm.services.records.rdm_complete_record_schema import RDMRecordMetadataSchemaPreset
from .rdm_metadata import RDMMetadataPreset

if TYPE_CHECKING:
    from oarepo_model.api import FunctionalPreset
    from oarepo_model.presets import Preset


class RDMMinimalMetadataPreset(RDMMetadataPreset):
    """Preset for RDM minimal metadata schema."""

    kind = "minimal"


class RDMBasicMetadataPreset(RDMMetadataPreset):
    """Preset for RDM basic metadata schema."""

    kind = "basic"


class RDMCompleteMetadataPreset(RDMMetadataPreset):
    """Preset for RDM complete metadata schema."""

    kind = "complete"


rdm_complete_preset: list[type[Preset | FunctionalPreset]] = [
    *rdm_static_preset,
    RDMRecordMetadataSchemaPreset,
    RDMCompleteMetadataPreset,
]
rdm_basic_preset: list[type[Preset | FunctionalPreset]] = [
    *rdm_static_preset,
    RDMBasicMetadataPreset,
]
rdm_minimal_preset: list[type[Preset | FunctionalPreset]] = [
    *rdm_static_preset,
    RDMMinimalMetadataPreset,
]

__all__ = ("rdm_basic_preset", "rdm_complete_preset", "rdm_minimal_preset")
