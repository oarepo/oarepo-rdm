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
from typing import TYPE_CHECKING

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


def finalize_app(app: Flask) -> None:
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

    _populate_facet_configs(app)


def _populate_facet_configs(app: Flask) -> None:
    """Derive RDM_FACETS and per-view facet lists from per-model search options.

    The multiplexed search options already merge facets across all registered
    models for each view (published / drafts / versions). Here we project that
    merged state onto the Flask config keys read by the FE search apps so the
    UI selections cannot drift from the backend aggregations.
    """
    ext: OARepoRDM = app.extensions["oarepo-rdm"]

    published = dict(ext.search_options.facets)
    drafts = dict(ext.draft_search_options.facets)
    # versions = dict(ext.versions_search_options.facets)

    # Build RDM_FACETS pool from per-model search options. FE expects the
    # `{"facet": TermsFacet, "ui": {...}}` wrapper shape; per-model search
    # options expose the raw TermsFacet, so wrap with a default `ui.field`.
    app.config["RDM_FACETS"] = {
        name: {"facet": facet, "ui": {"field": name}} for name, facet in {**drafts, **published}.items()
    }

    # FE search apps read `<CONFIG>["facets"]` as the *selected* names to render.
    # Backend services already aggregate exactly those, via the same merge.
    _set_facets(app.config, "RDM_SEARCH", published)
    _set_facets(app.config, "RDM_SEARCH_DRAFTS", drafts)
    # _set_facets(app.config, "RDM_SEARCH_VERSIONING", versions)
    # Community records reuse the published search backend.
    _set_facets(app.config, "COMMUNITIES_RECORDS_SEARCH", published)


def _set_facets(config: dict, key: str, facets: dict) -> None:
    config[key] = {**config.get(key, {}), "facets": list(facets.keys())}
