#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Component that sets default pids on empty records based on DOI configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask import current_app
from oarepo_ui.resources.components import UIResourceComponent

if TYPE_CHECKING:
    from oarepo_ui.resources.records.resource import RecordsUIResource


class EmptyRecordPidsComponent(UIResourceComponent):
    """Sets default pids structure on empty records based on DOI provider config."""

    resource: RecordsUIResource

    @override
    def empty_record(self, *, empty_data: dict, **kwargs: Any) -> None:
        """Set default pids on the empty record.

        :param empty_data: empty record data
        """
        pids_providers = getattr(self.resource.api_config, "pids_providers", None)

        if pids_providers and "doi" in pids_providers:
            if (
                current_app.config["RDM_PERSISTENT_IDENTIFIERS"].get("doi", {}).get("ui", {}).get("default_selected")
                == "yes"  # yes, no or not_needed
            ):
                empty_data["pids"] = {"doi": {"provider": "external", "identifier": ""}}
            else:
                empty_data["pids"] = {}
        else:
            empty_data["pids"] = {}
