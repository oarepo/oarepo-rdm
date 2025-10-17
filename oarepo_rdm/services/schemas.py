#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Custom schema fields for RDM UI schema."""

from __future__ import annotations

from contextvars import ContextVar
from functools import partial
from typing import TYPE_CHECKING, Any

from invenio_rdm_records.resources.serializers.ui.schema import (
    make_affiliation_index as invenio_rdm_make_affiliation_index,
)
from marshmallow import fields

if TYPE_CHECKING:
    from collections.abc import Mapping

    from marshmallow.utils import _Missing

ui_serialized_record = ContextVar[Any]("ui_serialized_record")


def make_affiliation_index(attr: str, _obj: Mapping[str, Any], *args: Any) -> Mapping[str, Any] | _Missing:
    """Convert creators/contributors to affiliation index.

    Invenio RDM uses hand-crafted UI serialization to convert record to UI representation.
    In CESNET implementation, we use automatic conversion that works independently for
    the main record and for the contained metadata.

    When this function is called, we are serializing the metadata part of the record.

    As invenio's make_affiliation_index expects the full record object, we need to
    store it in a context variable during serialization
    (happens in the oarepo_rdm.model.resources.records.ui_json_serializer) and
    retrieve it here.
    """
    return invenio_rdm_make_affiliation_index(attr, ui_serialized_record.get(), *args)


class RDMCreatorUIField(fields.Function):
    """Custom field for RDM Creator."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Create the field."""
        super().__init__(partial(make_affiliation_index, "creators"), *args, **kwargs)


class RDMContributorUIField(fields.Function):
    """Custom field for RDM Contributor."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Create the field."""
        super().__init__(
            partial(make_affiliation_index, "contributors"),
            *args,
            **kwargs,
        )
