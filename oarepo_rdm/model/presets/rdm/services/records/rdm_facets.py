# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate RDM-specific facets (access_status)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services import facets as rdm_facets
from oarepo_model.customizations import (
    AddToDictionary,
    AddToModule,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMFacetsPreset(Preset):
    """Preset for RDM-specific facets (access_status)."""

    provides = ("RDMFacets",)
    modifies = ("RecordFacets",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        rdm = {
            "access_status": rdm_facets.access_status,
        }

        for name, facet in rdm.items():
            yield AddToModule("facets", name, facet)

        yield AddToDictionary("RecordFacets", rdm)
