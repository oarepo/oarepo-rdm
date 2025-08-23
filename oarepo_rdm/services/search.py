from __future__ import annotations

from deepmerge import always_merger
from invenio_records_resources.services.records.config import SearchOptions
from invenio_records_resources.services.records.params import (
    PaginationParam,
    ParamInterpreter,
    SortParam,
)
from oarepo_runtime import current_runtime
from oarepo_runtime.services.facets.params import GroupedFacetsParam


class DelegatedQueryParam(ParamInterpreter):
    """Evaluate the 'json' parameter."""

    def apply(self, identity, search, params):
        """Evaluate the query str on the search."""
        if "delegated_query" in params:
            queries_list, search_opts = params.pop("delegated_query")

            query, aggs, post_filter, sort = self._merge_queries(
                queries_list, params, search_opts
            )

            for agg in aggs:
                search.aggs.bucket(agg, aggs[agg])
            search = search.query(query)
            if post_filter != {}:
                search = search.post_filter(post_filter)
            if sort:
                search = search.sort(sort[0])
        return search

    def _merge_queries(
        self, queries_list: dict[str, dict], params, search_opts
    ) -> (dict, dict, dict, list):
        """Merge multiple queries into a single query."""
        query = {"bool": {"should": [], "minimum_should_match": 1}}
        aggs = {}
        post_filter = {}
        sort = []

        for pid_type, query_data in queries_list.items():
            schema_query = query_data.get("query", {})
            query["bool"]["should"].append(
                {"bool": {"must": [{"term": {"$schema": pid_type}}, schema_query]}}
            )

            if "aggs" in query_data:
                for agg_key, agg_value in query_data["aggs"].items():
                    aggs[agg_key] = agg_value
            if "post_filter" in query_data:
                for post_key, post_value in query_data["post_filter"].items():
                    post_filter[post_key] = post_value
            if "sort" in query_data:
                sort.extend(query_data["sort"])

        return query, aggs, post_filter, sort


class MultiplexedSearchOptions(SearchOptions):
    """Search options."""

    params_interpreters_cls = [
        GroupedFacetsParam,
        PaginationParam,
        SortParam,
        DelegatedQueryParam,
    ]

    def __init__(self, config_field) -> None:
        search_opts = self._search_opts(config_field)

        self.facets = search_opts["facets"]
        self.facet_groups = search_opts["facet_groups"]
        self.sort_options = search_opts["sort_options"]
        self.sort_default = search_opts["sort_default"]
        self.sort_default_no_query = search_opts["sort_default_no_query"]

    def _search_opts_from_search_obj(self, search):
        facets = {}
        sort_options = {}

        facets.update(search.facets)
        try:
            sort_options.update(search.sort_options)
        except:
            pass
        sort_default = search.sort_default
        sort_default_no_query = search.sort_default_no_query
        facet_groups = getattr(search, "facet_groups", {})
        return {
            "facets": facets,
            "facet_groups": facet_groups,
            "sort_options": sort_options,
            "sort_default": sort_default,
            "sort_default_no_query": sort_default_no_query,
        }

    def _search_opts(self, config_field):
        ret = {}
        for model in current_runtime.rdm_models:
            if hasattr(model.service.config, config_field):
                ret = always_merger.merge(
                    ret,
                    self._search_opts_from_search_obj(
                        getattr(model.service.config, config_field)
                    ),
                )
        return ret
