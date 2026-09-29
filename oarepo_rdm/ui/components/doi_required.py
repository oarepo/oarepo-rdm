# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Component that sets is_doi_required in the deposit form config."""

from __future__ import annotations

from typing import Any, override

from flask import current_app
from oarepo_ui.resources.components import UIResourceComponent


class DoiRequiredComponent(UIResourceComponent):
    """Adds is_doi_required flag to the deposit form config from RDM app config."""

    @override
    def form_config(self, *, form_config: dict, **kwargs: Any) -> None:
        """Set is_doi_required in the form config.

        :param form_config: form configuration dictionary
        """
        form_config["is_doi_required"] = (
            current_app.config.get("RDM_PERSISTENT_IDENTIFIERS", {}).get("doi", {}).get("required")
        )
