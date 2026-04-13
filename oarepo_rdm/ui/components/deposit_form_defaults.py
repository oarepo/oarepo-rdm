#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Component that applies APP_RDM_DEPOSIT_FORM_DEFAULTS to empty records."""

from __future__ import annotations

from typing import Any, override

from flask import current_app
from invenio_app_rdm.records_ui.utils import set_default_value
from oarepo_ui.resources.components import UIResourceComponent


class DepositFormDefaultsComponent(UIResourceComponent):
    """Applies deposit form default values from app config to empty records."""

    @override
    def empty_record(self, *, empty_data: dict, **kwargs: Any) -> None:
        """Apply APP_RDM_DEPOSIT_FORM_DEFAULTS to the empty record.

        :param empty_data: empty record data
        """
        defaults = current_app.config.get("APP_RDM_DEPOSIT_FORM_DEFAULTS") or {}
        for key, value in defaults.items():
            set_default_value(empty_data, value, key)
