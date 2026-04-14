#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Component that injects a parent DOI into the draft UI when Datacite is enabled."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask import current_app
from invenio_rdm_records.proxies import current_rdm_records
from oarepo_runtime.typing import record_from_result
from oarepo_ui.resources.components import UIResourceComponent

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records_resources.services.records.results import RecordItem


class InjectParentDoiComponent(UIResourceComponent):
    """Injects a parent DOI into the draft UI if Datacite is enabled and required."""

    @override
    def before_ui_detail(
        self,
        *,
        api_record: RecordItem,
        identity: Identity,
        render_kwargs: dict,
        **kwargs: Any,
    ) -> None:
        """Inject parent DOI into record_ui for draft preview pages.

        :param api_record: the record being displayed
        :param render_kwargs: the full render context containing record_ui, is_preview, is_draft
        """
        is_preview = render_kwargs.get("is_preview", False)
        is_draft = render_kwargs.get("is_draft", False)
        record_ui = render_kwargs.get("record_ui", {})

        if not (is_preview and is_draft):
            return

        if not current_app.config.get("DATACITE_ENABLED"):
            return

        service = current_rdm_records.records_service
        datacite_providers = [
            v["datacite"] for p, v in service.config.parent_pids_providers.items() if p == "doi" and "datacite" in v
        ]
        if not datacite_providers:
            return

        datacite_provider = datacite_providers[0]
        should_mint_parent_doi = True

        is_doi_required = current_app.config.get("RDM_PARENT_PERSISTENT_IDENTIFIERS", {}).get("doi", {}).get("required")
        if not is_doi_required:
            pids = getattr(record_from_result(api_record), "pids", {})
            record_doi = pids.get("doi", {})
            is_doi_reserved = record_doi.get("provider", "") == "datacite" and record_doi.get("identifier")
            if not is_doi_reserved:
                should_mint_parent_doi = False

        if should_mint_parent_doi:
            parent = getattr(record_from_result(api_record), "parent", None)
            if parent:
                parent_doi = datacite_provider.client.generate_doi(parent)
                record_ui.setdefault("ui", {})["new_draft_parent_doi"] = parent_doi
            else:
                raise ValueError(f"Record {api_record['id']} has no parent field.")  # PRAGMA: no cover
