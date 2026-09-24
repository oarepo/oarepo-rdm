# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating RDM record.

This module provides a preset that modifies record API class to RDM compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.records.api import Record as InvenioRecord
from invenio_rdm_records.records.api import RDMRecord
from oarepo_model.customizations import Customization, ReplaceBaseClass
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMRecordPreset(Preset):
    """Preset for record service class."""

    modifies = ("Record",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ReplaceBaseClass("Record", InvenioRecord, RDMRecord)
