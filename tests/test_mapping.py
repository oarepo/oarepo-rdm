#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests to checks that RDM mapping is complete."""
import json
from oarepo_model.utils import resolve_file_content
"""
from __future__ import annotations

import json
from pathlib import Path

import invenio_rdm_records
import pytest
from invenio_rdm_records.records.api import RDMDraft, RDMRecord

from oarepo_rdm.model.presets.rdm.records.rdm_mapping import load_mapping_patches
from tools.compare_rdm_mappings import read_live_mapping, run_comparison

# Capture these before OARepo replaces the upstream index names during app setup.
RDM_MAPPING_VERSIONS = (
    ("drafts", "draft", RDMDraft.index._name.rsplit("draft-", maxsplit=1)[1]),  # noqa: SLF001
    ("records", "record", RDMRecord.index._name.rsplit("record-", maxsplit=1)[1]),  # noqa: SLF001
)


def comparison_section(output: str, title: str) -> str:

    return output.split(f"\n{title} (", maxsplit=1)[1].split("\n\n", maxsplit=1)[0]


@pytest.mark.parametrize(
    ("mapping_directory", "mapping_kind", "mapping_version"), RDM_MAPPING_VERSIONS, ids=["draft", "record"]
)
def test_compare_rdm_mappings(app, rdm_mapping_model, capsys, mapping_directory, mapping_kind, mapping_version):

    model_name = rdm_mapping_model.oarepo_model_arguments["code"]
    mappings_root = Path(invenio_rdm_records.__file__).parent / "records" / "mappings" / "os-v2" / "rdmrecords"

    result = run_comparison(
        argparse.Namespace(
            json_mapping=mappings_root / mapping_directory / f"{mapping_kind}-{mapping_version}.json",
            appcontext=model_name,
            python_mapping=None,
        )
    )
    output = capsys.readouterr().out
    assert result == 1  # The complete generated mapping currently differs from upstream.
    assert f"Python: live model {model_name!r}" in output
    supplied = output.split("\nRDMMappingPreset differences", maxsplit=1)[0]
    assert "  $.mappings.properties.metadata\n" in supplied
    assert "  $.mappings.properties.created\n" in supplied
    assert "ONLY IN JSON    $.mappings.properties.metadata\n" not in output
    assert "$.mappings.properties.access.properties.files.ignore_above" in comparison_section(
        output, "RDMMappingPreset differences"
    )
    assert "$.mappings.properties.metadata.properties.publication_date.type" in comparison_section(
        output, "Other preset / model generation differences"
    )
    assert "$.mappings.properties.media_files.properties.entries" in comparison_section(
        output, "Invenio-only fields / options"
    )
    # Keep the diagnostic report visible with pytest -s.
    print(output, end="")  # noqa: T201


@pytest.mark.parametrize("mapping_kind", ["draft"])
def test_compare_rdm_mappings_classifies_live_differences(app, rdm_mapping_model, tmp_path, capsys, mapping_kind):

    model_name = rdm_mapping_model.oarepo_model_arguments["code"]
    live_mapping, _ = read_live_mapping(model_name, mapping_kind)
    symbolic_file = getattr(rdm_mapping_model, f"{mapping_kind}-mapping")
    final_file_path = f"{symbolic_file['module-name']}/{symbolic_file['file-path']}"
    assert live_mapping == json.loads(rdm_mapping_model.__files__[final_file_path])
    json_mapping = tmp_path / f"{mapping_kind}-comparison.json"
    args = argparse.Namespace(json_mapping=json_mapping, appcontext=model_name, python_mapping=None)

    json_mapping.write_text(json.dumps(live_mapping))
    assert run_comparison(args) == 0
    identical_output = capsys.readouterr().out
    assert "  $.mappings.properties.metadata\n" in identical_output
    assert "0 differing path(s)." in identical_output

    properties = live_mapping["mappings"]["properties"]
    properties["access"]["properties"]["files"]["type"] = "text"
    properties["metadata"]["properties"]["title"]["type"] = "integer"
    del properties["is_published"]
    properties["parent"]["properties"]["upstream_added"] = {"type": "keyword"}
    properties["metadata"]["properties"]["upstream_added"] = {"type": "keyword"}
    properties["uuid"]["index"] = False
    live_mapping["mappings"]["dynamic_templates"].append({"upstream_added": {"mapping": {"type": "keyword"}}})
    json_mapping.write_text(json.dumps(live_mapping))

    assert run_comparison(args) == 1
    output = capsys.readouterr().out
    preset = comparison_section(output, "RDMMappingPreset differences")
    other = comparison_section(output, "Other preset / model generation differences")
    invenio_only = comparison_section(output, "Invenio-only fields / options")
    assert preset.startswith("2):\n")
    assert "VALUE CHANGED   $.mappings.properties.access.properties.files.type" in preset
    assert "ONLY IN PYTHON  $.mappings.properties.is_published" in preset
    assert other.startswith("1):\n")
    assert "VALUE CHANGED   $.mappings.properties.metadata.properties.title.type" in other
    assert invenio_only.startswith("4):\n")
    assert "$.mappings.properties.parent.properties.upstream_added" in invenio_only
    assert "$.mappings.properties.metadata.properties.upstream_added" in invenio_only
    assert "$.mappings.properties.uuid.index = false" in invenio_only
    assert "$.mappings.dynamic_templates[3]" in invenio_only
    assert "7 differing path(s)." in output


@pytest.mark.parametrize(
    ("model_fixture", "custom_field"),
    [
        ("model_a", "adescription"),
        ("model_b", "bdescription"),
        ("model_c", "cdescription"),
        ("rdm_mapping_model", None),
    ],
)
@pytest.mark.parametrize("mapping_kind", ["draft", "record"])
def test_upstream_rdm_mapping_preserves_generated_fields(app, request, model_fixture, custom_field, mapping_kind):

    declared_model = request.getfixturevalue(model_fixture)
    mapping, _ = read_live_mapping(declared_model.oarepo_model_arguments["code"], mapping_kind)
    if custom_field:
        assert mapping["settings"]["index.query.default_field"] == ["metadata.title", f"metadata.{custom_field}"]
    else:
        assert "settings" not in mapping
    mapping = mapping["mappings"]
    assert mapping["dynamic"] == "strict"
    assert "date_detection" not in mapping
    assert "numeric_detection" not in mapping
    properties = mapping["properties"]
    assert properties["$schema"] == {"type": "keyword"}
    assert properties["uuid"] == {"type": "keyword"}
    assert properties["version_id"] == {"type": "integer"}
    assert properties["metadata"]["dynamic"] == "strict"
    if custom_field:
        assert properties["metadata"]["properties"][custom_field] == {"type": "keyword", "ignore_above": 256}
    assert properties["files"]["properties"]["enabled"] == {"type": "boolean"}
    assert "entries" in properties["files"]["properties"]
    assert properties["media_files"] == {"type": "object", "properties": {"enabled": {"type": "boolean"}}}
    assert "review" not in properties

    parent = properties["parent"]["properties"]
    assert parent["id"] == {"type": "keyword"}
    assert "permission_flags" not in parent
    assert "review" not in parent
    entries = parent["communities"]["properties"]["entries"]
    for community in (entries, entries["properties"]["parent"]):
        metadata = community["properties"]["metadata"]["properties"]
        award = metadata["funding"]["properties"]["award"]["properties"]
        assert "organizations" not in award
        assert "subjects" not in award
        assert "identifiers" not in metadata["organizations"]["properties"]

    access = properties["access"]
    assert access["type"] == "object"
    embargo = access["properties"]["embargo"]
    assert embargo["type"] == "object"
    assert embargo["properties"]["until"]["format"] == "basic_date||strict_date"
    for field in ("files", "record", "status"):
        assert access["properties"][field]["ignore_above"] == 1024
    assert properties["deletion_status"]["ignore_above"] == 1024
    if mapping_kind == "record":
        assert "stats" in properties
        assert "deletion_policy" not in properties["tombstone"]["properties"]
    else:
        assert "stats" not in properties
        assert "tombstone" not in properties


def test_upstream_rdm_mapping_patches_are_fresh(app):

    parent, record = load_mapping_patches()
    parent["mappings"]["dynamic_templates"][0]["pids"]["path_match"] = "changed.*"
    record["mappings"]["properties"]["tombstone"]["properties"]["note"]["type"] = "keyword"
    another_parent, another_record = load_mapping_patches()
    assert another_parent["mappings"]["dynamic_templates"][0]["pids"]["path_match"] == "pids.*"
    assert another_record["mappings"]["properties"]["tombstone"]["properties"]["note"]["type"] == "text"

from oarepo_model.utils import resolve_file_content


def test_mapping_rdm_complete(app, model_c):

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
    """
import os
def test_save_mappings(model_c):
    mapping_key = "mappings/os-v2/modelc/metadata-v1.0.0.json"
    mapping_content = json.loads(resolve_file_content(model_c.__files__[mapping_key]))
    del mapping_content["mappings"]["properties"]["metadata"]
    with open(os.path.join(os.path.dirname(__file__), "oarepo_mapping.json"), "w") as f:
        f.write(json.dumps(mapping_content, indent=2, sort_keys=True))
    invenio_mapping = ("/home/ron/prace/oarepo-rdm/"
                       ".venv/lib/python3.14/site-packages/invenio_rdm_records/"
                       "records/mappings/os-v2/rdmrecords/records/record-v7.0.0.json")
    with open(invenio_mapping, "r") as f:
        mapping_content = json.loads(f.read())
        del mapping_content["mappings"]["properties"]["metadata"]

    with open(os.path.join(os.path.dirname(__file__), "invenio_mapping.json"), "w") as f:
        f.write(json.dumps(mapping_content, indent=2, sort_keys=True))


def test_save_draft_mappings(model_c):
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
