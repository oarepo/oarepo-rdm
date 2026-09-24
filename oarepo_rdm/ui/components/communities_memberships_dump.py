# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""UI Resource component for community memberships."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_app_rdm.records_ui.views.deposits import get_user_communities_memberships
from oarepo_ui.resources.components import UIResourceComponent

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records_resources.services.records.results import RecordItem


class CommunitiesMembershipsComponent(UIResourceComponent):
    """Pass current identity's community memberships to form config."""

    @override
    def form_config(
        self,
        *,
        api_record: RecordItem,
        record: dict,
        identity: Identity,
        form_config: dict,
        ui_links: dict,
        extra_context: dict,
        **kwargs: Any,
    ) -> None:
        """Add current identity's community memberships to form config."""
        form_config["user_communities_memberships"] = get_user_communities_memberships()
