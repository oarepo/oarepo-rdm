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

from oarepo_ui.resources import (
    AllowedHtmlTagsComponent,
    BabelComponent,
    CustomFieldsComponent,
    PermissionsComponent,
    RecordsUIResourceConfig,
)

from oarepo_rdm.ui.components import (
    CommunitiesMembershipsComponent,
    RDMVocabularyOptionsComponent,
)
from tests.test_ui.ui.common import ModelUISerializer

if TYPE_CHECKING:
    from collections.abc import Mapping


class ModelaUIResourceConfig(RecordsUIResourceConfig):
    """UI resource config for the ModelA."""

    api_service = "modela"
    model_name = "modela"

    blueprint_name = "modela_ui"
    url_prefix = "/modela"
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
        CommunitiesMembershipsComponent,
        RDMVocabularyOptionsComponent,
    )
