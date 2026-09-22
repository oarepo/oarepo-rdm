# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating RDM record resource.

This module provides a preset that modifies record resource to RDM compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.resources import RecordResource as DraftRecordResource
from invenio_rdm_records.resources.resources import (
    RDMRecordResource as RDMBaseRecordResource,
)
from oarepo_model.customizations import Customization, ReplaceBaseClass
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMRecordResourcePreset(Preset):
    """Preset for record resource class."""

    modifies = ("RecordResource",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ReplaceBaseClass("RecordResource", DraftRecordResource, RDMBaseRecordResource)
