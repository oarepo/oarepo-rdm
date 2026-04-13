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

from oarepo_rdm.ui.config import RDMRecordsUIResourceConfig
from tests.test_ui.ui.common import ModelUISerializer

if TYPE_CHECKING:
    from collections.abc import Mapping


class ModelcUIResourceConfig(RDMRecordsUIResourceConfig):
    """UI resource config for the ModelC."""

    api_service = "modelc"  # must be something included in oarepo, as oarepo is used in tests
    model_name = "modelc"
    blueprint_name = "modelc_ui"
    url_prefix = "/modelc"
    ui_serializer_class = ModelUISerializer
    templates: Mapping = {
        **RDMRecordsUIResourceConfig.templates,
        "detail": "TestDetail",
        "search": "TestSearch",
        "create": "test.TestCreate",
        "edit": "TestEdit",
    }
