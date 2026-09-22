# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""UI Resource component for vocabulary search."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_app_rdm.records_ui.views.deposits import (
    VocabulariesOptions,
)
from oarepo_ui.resources.components import UIResourceComponent

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records_resources.services.records.results import RecordItem


class RDMVocabularyOptionsComponent(UIResourceComponent):
    """Pass RDM vocabulary fixtures to form config."""

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
        """Add smaller RDM vocabularies to form config."""
        form_config["vocabularies"] = VocabulariesOptions().dump()  # pragma: no cover
