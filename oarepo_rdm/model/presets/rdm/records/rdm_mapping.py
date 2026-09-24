# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating RDM search mapping.

This module provides a preset that modifies search mapping to RDM compatibility.
"""

from __future__ import annotations

import json
import logging
import re
from importlib.resources import files
from typing import TYPE_CHECKING, Any, cast, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Generator
    from importlib.resources.abc import Traversable

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

        def check_latest_version(path: Traversable, file: str) -> None:
            grps = re.compile(r"(.*)-v(\d+)\.(\d+)\.(\d+)").match(file).groups()  # type: ignore[union-attr]
            type_ = grps[0]
            version = [int(v) for v in grps[1:]]
            version_pattern = re.compile(rf"{type_}-v(\d+)\.(\d+)\.(\d+)$")
            files_ = [
                entry.name.removesuffix(".json")
                for entry in path.iterdir()
                if entry.is_file() and entry.name.endswith(".json")
            ]
            versions = [
                [int(part) for part in match.groups()]
                for mapping_file in files_
                if (match := version_pattern.fullmatch(mapping_file))
            ]
            latest_version = max(versions)
            if latest_version != version:
                logger.warning(
                    "Invenio RDM mapping version of %s is not up to date, use %s",
                    type_,
                    latest_version,
                )
            if len(files_) > len(versions):
                logger.warning("New mapping file type found in invenio rdm mappings.")

        def filter_rdm_mapping(path: Traversable) -> dict[str, Any]:
            mapping = json.loads(path.read_text(encoding="utf-8"))
            del mapping["mappings"]["properties"]["metadata"]
            del mapping["mappings"]["properties"]["$schema"]["index"]
            if "settings" in mapping and "index.query.default_field" in mapping["settings"]:
                del mapping["settings"]["index.query.default_field"]
            return cast("dict[str, Any]", mapping)

        draft_folder = files("invenio_rdm_records") / "records/mappings/os-v2/rdmrecords/drafts"
        record_folder = files("invenio_rdm_records") / "records/mappings/os-v2/rdmrecords/records"

        check_latest_version(draft_folder, "draft-v6.0.0.json")
        check_latest_version(record_folder, "record-v7.0.0.json")
        rdm_draft_mapping = filter_rdm_mapping(draft_folder / "draft-v6.0.0.json")
        rdm_record_mapping = filter_rdm_mapping(record_folder / "record-v7.0.0.json")

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
