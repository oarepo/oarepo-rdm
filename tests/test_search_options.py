#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Regression tests for model-specific search options and delegated queries."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from invenio_access.permissions import system_identity
from invenio_search.engine import dsl

from .models import modela, modelb


@pytest.mark.parametrize("config_field", [None, "search", "search_drafts", "search_versions"])
def test_delegated_search_uses_model_parsers_once(app, rdm_records_service, monkeypatch, config_field):
    """The selected model options parse q once within each schema's query."""
    global_service = rdm_records_service._get_current_object()  # noqa: SLF001 # monkeypatch the resolved service
    options_field = config_field or "search"
    global_options = getattr(global_service.config, options_field)
    global_parser = Mock(side_effect=AssertionError("The global query must use the delegated model queries"))
    monkeypatch.setattr(global_options, "query_parser_cls", global_parser)

    services = {}
    parsers = []
    expected_queries = {}
    for model, field in [(modela, "metadata.adescription"), (modelb, "metadata.bdescription")]:
        service = model.proxies.current_service._get_current_object()  # noqa: SLF001 # monkeypatch the resolved service
        schema = model.Record.schema.value
        services[schema] = service
        options = getattr(service.config, options_field)
        parser = Mock()
        parser.return_value.parse.return_value = dsl.Q("term", **{field: "needle"})
        option_cls = options if isinstance(options, type) else type(options)
        model_options = type("ModelSearchOptions", (option_cls,), {"query_parser_cls": parser})()
        monkeypatch.setattr(service.config, options_field, model_options)
        parsers.append(parser)
        expected_queries[schema] = {"term": {field: "needle"}}

    monkeypatch.setattr(global_service, "_search_eligible_services", lambda *_args, **_kwargs: services)
    search = global_service._search(  # noqa: SLF001 # inspect the generated DSL without executing a search
        options_field,
        system_identity,
        {"q": "needle"},
        None,
        search_opts=global_options if config_field else None,
        permission_action=None,
    )

    global_parser.assert_not_called()
    for parser in parsers:
        parser.assert_called_once_with(system_identity)
        parser.return_value.parse.assert_called_once_with("needle")

    branches = search.to_dict()["query"]["bool"]["should"]
    assert len(branches) == len(services)
    for branch in branches:
        schema_term, model_query = branch["bool"]["must"]
        schema = schema_term["term"]["$schema"]
        assert model_query["bool"]["must"] == [expected_queries[schema]]


@pytest.mark.parametrize("config_field", ["search", "search_versions"])
@pytest.mark.parametrize("shared_with_me", [False, True], ids=["owned", "shared"])
def test_sharing_flags_do_not_filter_published_or_version_queries(
    app, rdm_records_service, users, config_field, shared_with_me
):
    """Draft sharing flags leave published and version queries unchanged."""
    service = rdm_records_service._get_current_object()  # noqa: SLF001 # access the resolved service
    options = getattr(service.config, config_field)
    identity = users[0].identity
    baseline = service._search(  # noqa: SLF001 # compare the generated DSL without executing a search
        config_field, identity, {}, None, search_opts=options
    )
    with_flag = service._search(  # noqa: SLF001 # compare the generated DSL without executing a search
        config_field, identity, {"shared_with_me": shared_with_me}, None, search_opts=options
    )
    assert with_flag.to_dict() == baseline.to_dict()
