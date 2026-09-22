# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for configuring RDM file resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.resources.config import RDMDraftFilesResourceConfig, RDMRecordFilesResourceConfig
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


class RDMFileResourceConfigPreset(Preset):
    """Preset for RDM files resource config class."""

    modifies = ("FileResourceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ReplaceBaseClass(
            "FileResourceConfig",
            FileResourceConfig,
            RDMRecordFilesResourceConfig,
        )

        # RDMRecordFilesResourceConfig doesn't have vnd.inveniordm.v1+json so the drafts config is used instead
        yield AddToDictionary("file_response_handlers", RDMDraftFilesResourceConfig.response_handlers)  # type:ignore[reportArgumentType]
