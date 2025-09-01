#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring RDM service config ui links."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import (
    AddToDictionary,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMServiceConfigUILinks(Preset):
    """Preset for extra RDM service ui config links."""

    modifies = ("record_links_item",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        ui_blueprint_name = model.configuration.get("ui_blueprint_name")
        if not ui_blueprint_name:
            return

        yield AddToDictionary(
            "record_links_item",
            {
                # TODO: add parent_doi_html and self_doi_html to be RDM compatible
            },
        )
