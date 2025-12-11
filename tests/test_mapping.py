#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests to checks that RDM mapping is complete."""

from __future__ import annotations

import json


def test_mapping_rdm_complete(app, model_c):
    """Check that RDM mapping contains all expected fields."""
    mapping_key = "mappings/os-v2/modelc/metadata-v1.0.0.json"
    mapping_content = json.loads(model_c.__files__[mapping_key])
    assert set(mapping_content["mappings"]["properties"]["metadata"]["properties"].keys()) == {
        "cdescription",
        "resource_type",
        "creators",
        "title",
        "additional_titles",
        "publisher",
        "publication_date",
        "subjects",
        "contributors",
        "dates",
        "languages",
        "identifiers",
        "related_identifiers",
        "sizes",
        "formats",
        "version",
        "rights",
        "copyright",
        "description",
        "additional_descriptions",
        "locations",
        "funding",
        "references",
    }
