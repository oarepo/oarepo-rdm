#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating RDM search mapping.

This module provides a preset that modifies search mapping to RDM compatibility.
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import TYPE_CHECKING, Any, cast, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMMappingPreset(Preset):
    """Preset for record service class."""

    modifies = ("draft-mapping",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:

        def filter_rdm_mapping(path: str) -> dict[str, Any]:
            mapping = json.loads(files("invenio_rdm_records").joinpath(path).read_text(encoding="utf-8"))
            del mapping["mappings"]["properties"]["metadata"]
            del mapping["mappings"]["properties"]["$schema"]["index"]
            if "settings" in mapping and "index.query.default_field" in mapping["settings"]:
                del mapping["settings"]["index.query.default_field"]
            return cast("dict[str, Any]", mapping)

        rdm_draft_mapping = filter_rdm_mapping("records/mappings/os-v2/rdmrecords/drafts/draft-v6.0.0.json")
        rdm_record_mapping = filter_rdm_mapping("records/mappings/os-v2/rdmrecords/records/record-v7.0.0.json")

        local_mapping = {
            "mappings": {
                "properties": {
                    "access": {
                        "type": "object",
                        "properties": {
                            "embargo": {
                                "type": "object",
                                "properties": {"until": {"format": "basic_date||strict_date"}},
                            },
                            "files": {"ignore_above": 1024},
                            "record": {"ignore_above": 1024},
                            "status": {"ignore_above": 1024},
                        },
                    },
                    "deletion_status": {"ignore_above": 1024},
                }
            }
        }

        yield PatchJSONFile(
            "draft-mapping",
            rdm_draft_mapping,
        )

        yield PatchJSONFile(
            "record-mapping",
            rdm_record_mapping,
        )

        yield PatchJSONFile(
            "draft-mapping",
            local_mapping,
        )

        yield PatchJSONFile(
            "record-mapping",
            local_mapping,
        )
