# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating RDM record resource config.

This module provides a preset that modifies record resource config to RDM compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.resources import (
    RecordResourceConfig as DraftRecordResourceConfig,
)
from invenio_rdm_records.resources.config import (
    RDMRecordResourceConfig as RDMBaseRecordResourceConfig,
)
from oarepo_model.customizations import (
    Customization,
    ReplaceBaseClass,
)
from oarepo_model.customizations.prepend_mixin import PrependMixin
from oarepo_model.presets import Preset

from oarepo_rdm.resources.records.config import OARepoRDMRecordResourceConfigMixin

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMRecordResourceConfigPreset(Preset):
    """Preset for record resource config class."""

    modifies = ("RecordResourceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ReplaceBaseClass(
            "RecordResourceConfig",
            DraftRecordResourceConfig,
            RDMBaseRecordResourceConfig,
        )
        yield PrependMixin("RecordResourceConfig", OARepoRDMRecordResourceConfigMixin)
