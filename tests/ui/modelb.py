#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING

from oarepo_ui.resources.components import (
    AllowedHtmlTagsComponent,
    BabelComponent,
    CustomFieldsComponent,
    PermissionsComponent,
    RecordsUIResourceConfig,
)

from tests.ui.common import ModelUISerializer

if TYPE_CHECKING:
    from collections.abc import Mapping


class ModelbUIResourceConfig(RecordsUIResourceConfig):
    """UI resource config for the ModelB."""

    api_service = "simple_model"  # must be something included in oarepo, as oarepo is used in tests

    blueprint_name = "simple_model"
    url_prefix = "/simple-model"
    ui_serializer_class = ModelUISerializer
    templates: Mapping = {
        **RecordsUIResourceConfig.templates,
        "detail": "TestDetail",
        "search": "TestSearch",
        "create": "test.TestCreate",
        "edit": "TestEdit",
    }

    components = (
        BabelComponent,
        PermissionsComponent,
        AllowedHtmlTagsComponent,
        CustomFieldsComponent,
    )
