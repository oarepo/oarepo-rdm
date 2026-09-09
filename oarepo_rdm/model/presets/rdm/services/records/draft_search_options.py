#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""RDM Draft Search Options Preset."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services.records.config import SearchDraftsOptions
from invenio_rdm_records.services.config import RDMSearchDraftsOptions
from oarepo_model.customizations import Customization, ReplaceBaseClass
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMDraftSearchOptionsPreset(Preset):
    """Preset for extra RDM based Search Options."""

    modifies = ("DraftSearchOptions",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ReplaceBaseClass(
            "DraftSearchOptions",
            SearchDraftsOptions,
            RDMSearchDraftsOptions,
        )
