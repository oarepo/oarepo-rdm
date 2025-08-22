#
# Copyright (C) 2025 CESNET z.s.p.o.
#
# oarepo-requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""oarepo oaiserver serializer functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from lxml import etree


class OAISerializer(Protocol):
    """Protocol for Invenio OAI serializers."""

    def __call__(self, pid: Any, record: dict[str, Any], **serializer_kwargs: Any) -> etree.Element:
        """Transform search hit into OAI record.

        :param pid: the value of the persistent identifier
        :param record: the record to serialize as it came from the opensearch. Notably,
        the record has a ["_source"] property that contains the actual record data.
        :param serializer_kwargs: additional keyword arguments for the serializer
        """


def multiplexing_oai_serializer(
    pid: Any,
    record: dict[str, Any],
    model_serializers: dict[str, OAISerializer],
    **serializer_kwargs: Any,
) -> etree.Element:
    """Multiplexing OAI serializer that dispatches to the correct model serializer."""
    source = record["_source"]
    json_schema = source.get("$schema")
    if not json_schema:
        raise ValueError(f"Missing JSON schema on record {record}")
    return model_serializers[json_schema](pid, record, **serializer_kwargs)
