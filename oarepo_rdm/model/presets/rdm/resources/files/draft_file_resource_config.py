# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for configuring RDM draft file resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.resources.config import RDMDraftFilesResourceConfig
from invenio_records_resources.resources import FileResourceConfig
from oarepo_model.customizations import (
    AddToDictionary,
    Customization,
    ReplaceBaseClass,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMDraftFileResourceConfigPreset(Preset):
    """Preset for RDM draft files resource config class."""

    modifies = ("DraftFileResourceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ReplaceBaseClass(
            "DraftFileResourceConfig",
            FileResourceConfig,
            RDMDraftFilesResourceConfig,
        )

        # file_response_handlers are shared between drafts and published
        # REVIEW: mapping vs. dict conflict
        yield AddToDictionary("file_response_handlers", RDMDraftFilesResourceConfig.response_handlers)  # ty: ignore[invalid-argument-type]
