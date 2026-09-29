# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for extra top field."""

from __future__ import annotations

import json

from oarepo_model.utils import resolve_file_content

from .models import model_funct_preset, top_level_field


def test_extra_top_level_field() -> None:
    mapping_key = "mappings/os-v2/top_level_field/metadata-v1.0.0.json"
    mapping_content = json.loads(resolve_file_content(top_level_field.__files__[mapping_key]))
    content = mapping_content["mappings"]["properties"]
    assert "original_record" in content
    assert "metadata" in content
    assert "created" in content
    assert "pids" in content
    assert "parent" in content


def test_functional_preset_extra_top_level_field() -> None:
    mapping_key = "mappings/os-v2/model_funct_preset/metadata-v1.0.0.json"
    mapping_content = json.loads(resolve_file_content(model_funct_preset.__files__[mapping_key]))
    content = mapping_content["mappings"]["properties"]
    assert "original_record" in content
    assert "metadata" in content
    assert "created" in content
    assert "pids" in content
    assert "parent" in content
