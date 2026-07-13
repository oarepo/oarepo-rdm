#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Component that restricts a new record when its preselected community is restricted."""

from __future__ import annotations

from typing import Any, override

from oarepo_ui.resources.components import UIResourceComponent


class RestrictedFromCommunityComponent(UIResourceComponent):
    """Sets record access to "restricted" when creating into a restricted community.

    When a record is created with a preselected community, the record's access
    defaults to "public" (set by the empty-record components). If that community
    is itself restricted, submission is only allowed for restricted records, so
    this component overrides the record access to "restricted" to match.

    It runs on ``before_ui_create``, i.e. after the empty record defaults have
    been applied, so its override wins.
    """

    @override
    def before_ui_create(
        self,
        *,
        data: dict,
        render_kwargs: dict,
        **kwargs: Any,
    ) -> None:
        """Restrict the empty record if the preselected community is restricted.

        :param data: empty API-serialized record data for the create form.
        :param render_kwargs: template render context, carrying ``community_ui``.
        """
        community_ui = render_kwargs.get("community_ui")
        if not community_ui:
            return

        if community_ui.get("access", {}).get("visibility") == "restricted":
            access = data.setdefault("access", {})
            access["record"] = "restricted"
            access["files"] = "restricted"
