#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see http://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring RDM file service.

This module provides a preset that replaces file service base class with the RDM one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services.files.service import RDMFileService
from invenio_records_resources.services.files import FileService
from oarepo_model.customizations import (
    Customization,
    ReplaceBaseClass,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMFileServicePreset(Preset):
    """Preset for RDM file service class."""

    modifies = ("FileService",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ReplaceBaseClass("FileService", old_base_class=FileService, new_base_class=RDMFileService)
