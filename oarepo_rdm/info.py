# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Component for handling repository info endpoint."""

from __future__ import annotations

from typing import override

from invenio_base.urls import invenio_url_for
from oarepo_runtime.info.views import InfoComponent


class RDMInfoComponent(InfoComponent):
    """RDM repository info endpoint component."""

    @override
    def repository(self, data: dict) -> None:
        """Modify repository info endpoint data."""
        data["links"]["records"] = invenio_url_for("records.search")
        data["links"]["drafts"] = invenio_url_for("records.search_user_records")
