# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from oarepo_rdm.ui.config import RDMRecordsUIResourceConfig
from tests.test_ui.ui.common import ModelUISerializer


class ModelbUIResourceConfig(RDMRecordsUIResourceConfig):
    """UI resource config for the ModelB."""

    template_folder = "templates"
    api_service = "modelb"
    model_name = "modelb"
    blueprint_name = "modelb_ui"
    url_prefix = "/modelb"
    ui_serializer_class = ModelUISerializer
