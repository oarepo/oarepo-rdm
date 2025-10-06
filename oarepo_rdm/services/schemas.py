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

from functools import partial
from typing import Any

from invenio_rdm_records.resources.serializers.ui.schema import make_affiliation_index
from marshmallow import fields


class RDMCreatorUIField(fields.Function):
    """Custom field for RDM Creator."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Create the field."""
        super().__init__(partial(make_affiliation_index, "creators"), *args, **kwargs)


class RDMContributorUIField(fields.Function):
    """Custom field for RDM Contributor."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Create the field."""
        super().__init__(partial(make_affiliation_index, "contributors"), *args, **kwargs)
