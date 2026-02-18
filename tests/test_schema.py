#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Test for RDM metadata schema."""

from __future__ import annotations

import marshmallow as ma
from invenio_rdm_records.services.schemas.metadata import CreatorSchema
from invenio_rdm_records.services.schemas.metadata import (
    MetadataSchema as RDMMetadataSchema,
)

from tests.models import modelc


def test_schema():
    """Test that the schema is correctly generated.

    modelc has the complete preset.
    """
    schema = modelc.RecordSchema()

    assert isinstance(schema, ma.Schema)
    metadata_schema = schema.fields["metadata"].schema

    creators_schema = metadata_schema.fields["creators"].inner.schema
    assert isinstance(creators_schema, CreatorSchema)


def test_rdm_complete_metadata():
    schema = modelc.RecordSchema()

    rdm_fields = RDMMetadataSchema._declared_fields  # noqa SLF001
    model_fields = schema.fields["metadata"].nested()._declared_fields  # noqa SLF001

    assert set(rdm_fields.items()) <= set(model_fields.items())
    assert "cdescription" in model_fields
