#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for extra top field."""

from __future__ import annotations

import json

from .models import model_functional_preset, model_with_top_level_field


def test_extra_top_level_field() -> None:
    mapping_key = "mappings/os-v2/model_with_top_level_field/metadata-v1.0.0.json"
    mapping_content = json.loads(model_with_top_level_field.__files__[mapping_key])
    content = mapping_content["mappings"]["properties"]
    assert "original_record" in content
    assert "metadata" in content
    assert "created" in content
    assert "pids" in content
    assert "parent" in content


def test_functional_preset_extra_top_level_field() -> None:
    mapping_key = "mappings/os-v2/model_functional_preset/metadata-v1.0.0.json"
    mapping_content = json.loads(model_functional_preset.__files__[mapping_key])
    content = mapping_content["mappings"]["properties"]
    assert "original_record" in content
    assert "metadata" in content
    assert "created" in content
    assert "pids" in content
    assert "parent" in content
