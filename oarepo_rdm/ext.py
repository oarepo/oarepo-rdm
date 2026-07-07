#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-rdm is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""OARepo-Requests extension."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

from invenio_records_resources.records.systemfields import IndexField
from invenio_records_resources.records.systemfields.pid import PIDField

from oarepo_rdm.records.systemfields.pid import (
    OARepoDraftPIDFieldContext,
    OARepoPIDFieldContext,
)
from oarepo_rdm.services.search import MultiplexedSearchOptions

if TYPE_CHECKING:
    from flask import Flask
    from invenio_records_resources.services.records.config import SearchOptions


class OARepoRDM:
    """OARepo extension of Invenio-RDM."""

    def __init__(self, app: Flask | None = None) -> None:
        """Extension initialization."""
        if app:
            self.init_app(app)
            self.init_config(app)

    def init_app(self, app: Flask) -> None:
        """Initialize the application."""
        self.app = app
        app.extensions["oarepo-rdm"] = self

    def init_config(self, app: Flask) -> None:
        """Load config."""
        from . import config

        app.config.setdefault("RDM_PERSISTENT_IDENTIFIER_PROVIDERS", []).extend(
            config.RDM_PERSISTENT_IDENTIFIER_PROVIDERS
        )

        app.config.setdefault("RDM_PERSISTENT_IDENTIFIERS", {}).update(config.RDM_PERSISTENT_IDENTIFIERS)

        app.config.setdefault("INFO_ENDPOINT_COMPONENTS", []).extend(config.INFO_ENDPOINT_COMPONENTS)

    @cached_property
    def search_options(self) -> SearchOptions:
        """Return search options."""
        return MultiplexedSearchOptions("search")

    @cached_property
    def draft_search_options(self) -> SearchOptions:
        """Return draft search options."""
        return MultiplexedSearchOptions("search_drafts")

    @cached_property
    def versions_search_options(self) -> SearchOptions:
        """Return versions search options."""
        return MultiplexedSearchOptions("search_versions")

    @cached_property
    def all_search_options(self) -> SearchOptions:
        """Return all search options."""
        return MultiplexedSearchOptions("search_all")

    @cached_property
    def dynamic_rdm_facets(self) -> dict[str, dict[str, Any]]:
        """Return a merged facet registry combining draft and published search options.

        Draft facets are listed first; a published facet with the same name overrides
        the draft entry. Each value has the shape expected by the InvenioRDM facet
        configuration API: ``{"facet": <instance>, "ui": {"field": <name>}}``.
        """
        published = dict(self.search_options.facets)
        drafts = dict(self.draft_search_options.facets)

        return {name: {"facet": facet, "ui": {"field": name}} for name, facet in {**drafts, **published}.items()}

    @cached_property
    def dynamic_rdm_search(self) -> dict[str, Any]:
        """Return search configuration for published records.

        Includes facet names from the published search options and the standard sort
        order expected by the InvenioRDM UI (view/download counts are meaningful for
        publicly visible records).
        """
        return {
            "facets": list(self.search_options.facets.keys()),
            "sort": [
                "bestmatch",
                "newest",
                "oldest",
                "version",
                "mostviewed",
                "mostdownloaded",
            ],
        }

    @cached_property
    def dynamic_rdm_search_drafts(self) -> dict[str, Any]:
        """Return search configuration for draft records.

        Includes facet names from the draft search options and sort options relevant
        to in-progress work. Update-time sorts are included; view/download count sorts
        are excluded because drafts are not publicly visible.
        """
        return {
            "facets": list(self.draft_search_options.facets.keys()),
            "sort": ["bestmatch", "updated-desc", "updated-asc", "newest", "oldest", "version"],
        }


def finalize_app(_app: Flask) -> None:
    """Finalize app."""
    from invenio_rdm_records.records.api import RDMDraft as InvenioRDMDraft
    from invenio_rdm_records.records.api import RDMRecord as InvenioRDMRecord
    from oarepo_runtime.proxies import current_runtime

    # note: we need to monkeypatch RDM records as some parts of Invenio use the
    # record classes directly, not through the appropriate service.
    #
    # if this was not the case, we could have just set draft_cls and record_cls
    # on our service config.
    InvenioRDMRecord.pid = PIDField(context_cls=OARepoPIDFieldContext)  # type: ignore[assignment]
    InvenioRDMDraft.pid = PIDField(context_cls=OARepoDraftPIDFieldContext)  # type: ignore[assignment]
    InvenioRDMRecord.index = IndexField(  # type: ignore[assignment]
        "never-used-for-indexing-records-search-alias-used-instead",
        search_alias=[*current_runtime.published_indices],
    )
    InvenioRDMDraft.index = IndexField(  # type: ignore[assignment]
        "never-used-for-indexing-drafts-search-alias-used-instead",
        search_alias=[*current_runtime.draft_indices],
    )
