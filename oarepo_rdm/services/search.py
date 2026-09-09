#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Multiplexed search options and delegated query parameter."""

from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING, Any, override

from deepmerge import always_merger
from invenio_rdm_records.services.search_params import (
    MetricsParam,
    SharedOrMyDraftsParam,
)
from invenio_records_resources.services.records.config import SearchOptions
from invenio_records_resources.services.records.params import (
    FacetsParam,
    ParamInterpreter,
)
from oarepo_runtime import current_runtime
from oarepo_runtime.services.facets.params import GroupedFacetsParam

if TYPE_CHECKING:
    from invenio_access.permissions import Identity
    from invenio_search import RecordsSearchV2


log = logging.getLogger(__name__)


class DelegatedQueryParam(ParamInterpreter):
    """Evaluate the 'json' parameter."""

    @override
    def apply(self, identity: Identity, search: RecordsSearchV2, params: dict[str, Any]) -> RecordsSearchV2:
        """Evaluate the query str on the search."""
        if "delegated_query" in params:
            queries_list, _ = params.pop("delegated_query")

            query, aggs, post_filter, sort = self._merge_queries(queries_list)

            for agg in aggs:
                search.aggs.bucket(agg, aggs[agg])
            search = search.query(query)
            if post_filter != {}:
                search = search.post_filter(post_filter)
            if sort:
                search = search.sort(sort[0])
        return search

    def _merge_queries(
        self,
        queries_list: dict[str, dict],
    ) -> tuple[dict, dict, dict, list]:
        """Merge multiple queries into a single query."""
        shoulds: list[Any] = []
        query = {"bool": {"should": shoulds, "minimum_should_match": 1}}
        aggs = {}
        post_filter = {}
        sort = []

        for schema, query_data in queries_list.items():
            schema_query = query_data.get("query", {})
            shoulds.append({"bool": {"must": [{"term": {"$schema": schema}}, schema_query]}})

            if "aggs" in query_data:
                aggs.update(query_data["aggs"])
            if "post_filter" in query_data:
                post_filter.update(query_data["post_filter"])
            # REVIEW: every model's sort is collected but only sort[0] is applied below, so the
            #   dict iteration order decides which model's sort wins. Also aggs/post_filter are
            #   merged by plain dict.update - same-named facets from different models silently
            #   overwrite each other.
            if "sort" in query_data:
                sort.extend(query_data["sort"])

        return query, aggs, post_filter, sort


def update_param_interpreters(
    existing: tuple[type[ParamInterpreter], ...],
) -> tuple[type[ParamInterpreter], ...]:
    """Update the list of parameter interpreters."""
    existing_list = list(existing)
    # remove FacetsParam
    existing_list.remove(FacetsParam)
    existing_list.append(GroupedFacetsParam)
    existing_list.append(DelegatedQueryParam)
    existing_list.append(SharedOrMyDraftsParam)
    # REVIEW: this one list is shared by all four MultiplexedSearchOptions instances (search,
    #   search_drafts, search_versions, search_all), so SharedOrMyDraftsParam and MetricsParam are
    #   applied to published and versions search too. Upstream scopes them per search kind.
    # REVIEW: MultiplexedSearchOptions also inherits query_parser_cls = plain QueryParser, while
    #   every model uses QueryParser.factory(tree_transformer_cls=SearchQueryValidator). The
    #   outer QueryStrParam therefore parses `q` unvalidated - and re-applies it on top of the
    #   merged delegated query, which already contains it per model.

    # TODO: We should make this search-kind aware and consider query interpretation per service
    existing_list.append(MetricsParam)
    return tuple(existing_list)


class MultiplexedSearchOptions(SearchOptions):
    """Search options."""

    params_interpreters_cls = update_param_interpreters(SearchOptions.params_interpreters_cls)

    def __init__(self, config_field: str) -> None:
        """Initialize search options."""
        search_opts = self._search_opts(config_field)

        # TODO: we need to have a look at ClassVar typing !!!
        self.facets = search_opts["facets"]  # type: ignore[assignment]
        self.facet_groups = search_opts["facet_groups"]  # type: ignore[assignment]
        self.sort_options = search_opts["sort_options"]  # type: ignore[assignment]
        self.sort_default = search_opts["sort_default"]  # type: ignore[assignment]
        self.sort_default_no_query = search_opts["sort_default_no_query"]  # type: ignore[assignment]

    def _search_opts_from_search_obj(self, search: Any) -> dict[str, Any]:
        facets = copy.deepcopy(search.facets)
        try:
            sort_options = copy.deepcopy(search.sort_options)
        except AttributeError as e:
            sort_options = {}
            log.warning("Error updating sort options: %s", e)
        facet_groups = copy.deepcopy(search.facet_groups) if hasattr(search, "facet_groups") else {}
        sort_default = search.sort_default
        sort_default_no_query = search.sort_default_no_query
        return {
            "facets": facets,
            "facet_groups": facet_groups,
            "sort_options": sort_options,
            "sort_default": sort_default, # REVIEW: it could make more sense to allow defining explicitly rather than this "the last of the models win"
            "sort_default_no_query": sort_default_no_query,
        }

    def _search_opts(self, config_field: str) -> dict:
        """Get search options from the config."""
        ret: dict[str, Any] = {}
        for model in current_runtime.rdm_models:
            if hasattr(model.service.config, config_field):
                ret = always_merger.merge(
                    ret,
                    self._search_opts_from_search_obj(getattr(model.service.config, config_field)),
                )

        return ret
