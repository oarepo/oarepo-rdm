#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from oarepo_rdm.ui.config import RDMRecordsUIResourceConfig
from tests.test_ui.ui.common import ModelUISerializer


class ModelbUIResourceConfig(RDMRecordsUIResourceConfig):
    """UI resource config for the ModelB."""

    template_folder = "templates"
    api_service = "modelb"  # must be something included in oarepo, as oarepo is used in tests
    model_name = "modelb"
    blueprint_name = "modelb_ui"
    url_prefix = "/modelb"
    ui_serializer_class = ModelUISerializer
