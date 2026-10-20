# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for configuring RDM draft file service config.

This module provides a preset that replaces draft file service config base class with the RDM one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services import RDMFileDraftServiceConfig
from invenio_records_resources.services import (
    FileServiceConfig,
)
from oarepo_model.customizations import (
    Customization,
    PrependMixin,
    ReplaceBaseClass,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMDraftFileServiceConfigPreset(Preset):
    """Preset for RDM draft file service config class."""

    modifies = ("DraftFileServiceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RDMDraftFileServiceConfigMixin:
            # RDM's WithFileLinks metaclass builds file links from this, overriding any file_links_* mixins
            name_of_file_blueprint = f"{model.blueprint_base}_draft_files"

        yield ReplaceBaseClass(
            "DraftFileServiceConfig",
            old_base_class=FileServiceConfig,
            new_base_class=RDMFileDraftServiceConfig,
        )
        yield PrependMixin("DraftFileServiceConfig", RDMDraftFileServiceConfigMixin)
