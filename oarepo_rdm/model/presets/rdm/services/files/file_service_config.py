# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for configuring RDM file service config.

This module provides a preset that replaces file service config base class with the RDM one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services import RDMFileRecordServiceConfig
from invenio_records_resources.services import (
    FileServiceConfig,
)
from oarepo_model.customizations import (
    Customization,
    ReplaceBaseClass,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMFileServiceConfigPreset(Preset):
    """Preset for RDM file service config class."""

    modifies = ("FileServiceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ReplaceBaseClass(
            "FileServiceConfig",
            old_base_class=FileServiceConfig,
            new_base_class=RDMFileRecordServiceConfig,
        )
