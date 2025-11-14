#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""OAI exports."""

from __future__ import annotations

from typing import Any

from flask_resources import BaseListSchema, JSONSerializer, MarshmallowSerializer
from invenio_rdm_records.resources.serializers.dublincore import DublinCoreXMLSerializer
from marshmallow import Schema


class ModelaDublinCoreXMLSerializer(DublinCoreXMLSerializer):
    """Dublin core serializer for model a."""


class ModelbDublinCoreXMLSerializer(DublinCoreXMLSerializer):
    """Dublin core serializer for model b."""


class ModelcDublinCoreXMLSerializer(DublinCoreXMLSerializer):
    """Dublin core serializer for model c."""


class TestListSchema(BaseListSchema):
    """List schema for test serializer."""

    def get_hits(self, obj_list):
        """Get the hits and add test-ok flag."""
        ret = super().get_hits(obj_list)
        ret["test-ok"] = True
        return ret


class ModelaSchema(Schema):
    """Schema for model a test serializer."""

    def dump(self, obj: Any, *, many: bool | None = None) -> Any:
        """Dump the object and add test-ok flag."""
        data = super().dump(obj, many=many)
        data["test-a-ok"] = True
        return data


class ModelaTestSerializer(MarshmallowSerializer):
    """Test serializer for model a."""

    def __init__(self):
        """Initialize the serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=ModelaSchema,
            list_schema_cls=TestListSchema,
            schema_context=None,
            schema_kwargs=None,
        )


class ModelbSchema(Schema):
    """Schema for model b test serializer."""

    def dump(self, obj: Any, *, many: bool | None = None) -> Any:
        """Dump the object and add test-ok flag."""
        data = super().dump(obj, many=many)
        data["test-b-ok"] = True
        return data


class ModelbTestSerializer(MarshmallowSerializer):
    """Test serializer for model b."""

    def __init__(self):
        """Initialize the serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=ModelbSchema,
            list_schema_cls=TestListSchema,
            schema_context=None,
            schema_kwargs=None,
        )
