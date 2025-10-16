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

from copy import deepcopy
from functools import partial
from typing import TYPE_CHECKING, Any

from invenio_rdm_records.resources.serializers.ui.schema import make_affiliation_index
from marshmallow import fields

if TYPE_CHECKING:
    from collections.abc import Mapping


# TODO: do this properly
def make_affiliation_index_metadata_hack(
    attr: str, obj: Mapping[str, Any], *args: Any
) -> Mapping[str, Any] | fields._MissingType:  # type: ignore[reportAttributeAccessIssue]
    """Wrap make_affiliation_index to prevent crashing on metadata missing attr key."""
    return make_affiliation_index(attr, {"metadata": {attr: deepcopy(obj.get(attr))}}, *args)


class RDMCreatorUIField(fields.Function):
    """Custom field for RDM Creator."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Create the field."""
        super().__init__(partial(make_affiliation_index_metadata_hack, "creators"), *args, **kwargs)


class RDMContributorUIField(fields.Function):
    """Custom field for RDM Contributor."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Create the field."""
        super().__init__(partial(make_affiliation_index_metadata_hack, "contributors"), *args, **kwargs)
