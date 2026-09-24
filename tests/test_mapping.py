# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests to checks that RDM mapping is complete."""

from __future__ import annotations

import json

from oarepo_model.utils import resolve_file_content


def test_mapping_rdm_complete(app, model_c):
    """Check that RDM mapping contains all expected fields."""
    mapping_key = "mappings/os-v2/modelc/metadata-v1.0.0.json"
    mapping_content = json.loads(resolve_file_content(model_c.__files__[mapping_key]))
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


import os
def test_save_jsonschema(model_c):
    mapping_key = "jsonschemas/modelc-v1.0.0.json"
    mapping_content = json.loads(resolve_file_content(model_c.__files__[mapping_key]))
    # del mapping_content["properties"]["metadata"]
    with open(os.path.join(os.path.dirname(__file__), "oarepo_jsonschema_with_metadata.json"), "w") as f:
        f.write(json.dumps(mapping_content, indent=2, sort_keys=True))
    invenio_mapping = ("/home/ron/prace/oarepo-rdm/"
                       ".venv/lib/python3.14/site-packages/invenio_rdm_records/"
                       "records/jsonschemas/records/record-v6.0.0.json")
    with open(invenio_mapping, "r") as f:
        mapping_content = json.loads(f.read())
        # del mapping_content["properties"]["metadata"]

    with open(os.path.join(os.path.dirname(__file__), "invenio_jsonschema_with_metadata.json"), "w") as f:
        f.write(json.dumps(mapping_content, indent=2, sort_keys=True))


def test_save_draft_jsonschema(model_c):
    mapping_key = "mappings/os-v2/modelc/draft-metadata-v1.0.0.json"
    mapping_content = json.loads(resolve_file_content(model_c.__files__[mapping_key]))
    del mapping_content["mappings"]["properties"]["metadata"]
    with open(os.path.join(os.path.dirname(__file__), "oarepo_draft_mapping.json"), "w") as f:
        f.write(json.dumps(mapping_content, indent=2, sort_keys=True))
    invenio_mapping = ("/home/ron/prace/oarepo-rdm/"
                       ".venv/lib/python3.14/site-packages/invenio_rdm_records/"
                       "records/mappings/os-v2/rdmrecords/drafts/draft-v6.0.0.json")
    with open(invenio_mapping, "r") as f:
        mapping_content = json.loads(f.read())
        del mapping_content["mappings"]["properties"]["metadata"]

    with open(os.path.join(os.path.dirname(__file__), "invenio_draft_mapping.json"), "w") as f:
        f.write(json.dumps(mapping_content, indent=2, sort_keys=True))
