#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Configuration of the RDM service."""

from __future__ import annotations

from flask_principal import Identity
from invenio_rdm_records.services.config import RDMRecordServiceConfig
from invenio_records_resources.services.records.config import SearchOptions
from invenio_records_resources.services.records.params import (
    PaginationParam,
    ParamInterpreter,
)
from invenio_records_resources.services.records.service import ServiceSchemaWrapper
from oarepo_runtime import current_runtime
from oarepo_runtime.services.facets.params import GroupedFacetsParam

from oarepo_rdm.proxies import current_oarepo_rdm

from .results import MultiplexingResultList


class MultiplexingLinks:
    """Multiplexing links for the RDM service.

    Based on the record being serialized, the expansion is delegated
    to the appropriate service.
    """

    def expand(self, identity: Identity, record=None, **kwargs):
        schema = record["$schema"]
        delegated_model = current_runtime.rdm_models_by_schema[schema]
        delegated_service = delegated_model.service
        return delegated_service.links_item_tpl.expand(record=record, **kwargs)  # type:


class MultiplexingSchema(ServiceSchemaWrapper):
    """Multiplexing schema for the RDM service.

    Based on the record being (de)serialized, the schema loading and dumping
    is delegated to the appropriate service.
    """

    def load(self, data, schema_args=None, context=None, raise_errors=True):
        schema = data["$schema"]
        delegated_model = current_runtime.rdm_models_by_schema[schema]
        delegated_service = delegated_model.service
        return delegated_service.schema.load(
            data, schema_args=schema_args, context=context, raise_errors=raise_errors
        )

    def dump(self, data, schema_args=None, context=None):
        schema = data["$schema"]
        delegated_model = current_runtime.rdm_models_by_schema[schema]
        delegated_service = delegated_model.service
        return delegated_service.schema.dump(
            data, schema_args=schema_args, context=context
        )


class GlobalSearchJSONParam(ParamInterpreter):
    """Evaluate the 'json' parameter."""

    def apply(self, identity, search, params):
        """Evaluate the query str on the search."""
        if "json" in params:
            query = params["json"]["query"]
            aggs = params["json"]["aggs"]
            post_filter = params["json"]["post_filter"]
            for agg in aggs:
                search.aggs.bucket(agg, aggs[agg])
            search = search.query(query)
            if post_filter != {}:
                search = search.post_filter(post_filter)
            if params["json"].get("sort"):
                search = search.sort(params["json"]["sort"][0])
        return search


class GlobalSearchOptions(SearchOptions):
    """Search options."""

    params_interpreters_cls = [
        GroupedFacetsParam,
        PaginationParam,
        GlobalSearchJSONParam,
    ]


class OARepoRDMServiceConfig(RDMRecordServiceConfig):
    """OARepo extension to RDM record service configuration."""

    result_list_cls = MultiplexingResultList

    @property
    def search(self) -> SearchOptions:
        return current_oarepo_rdm.search_options

    @property
    def search_drafts(self) -> SearchOptions:
        return current_oarepo_rdm.draft_search_options

    @property
    def search_versions(self) -> SearchOptions:
        return current_oarepo_rdm.versions_search_options

    @property
    def search_all(self) -> SearchOptions:
        return current_oarepo_rdm.all_search_options
