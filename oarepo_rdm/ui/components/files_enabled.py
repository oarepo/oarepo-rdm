#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Component that sets the default files.enabled flag for empty records."""

from __future__ import annotations

from typing import Any, override

from flask import current_app
from oarepo_ui.resources.components import UIResourceComponent


class FilesEnabledComponent(UIResourceComponent):
    """Sets the default files.enabled value on empty records from RDM app config."""

    @override
    def empty_record(self, *, empty_data: dict, **kwargs: Any) -> None:
        """Set files.enabled on the empty record.

        :param empty_data: empty record data
        """
        empty_data.setdefault("files", {})["enabled"] = current_app.config.get("RDM_DEFAULT_FILES_ENABLED")
