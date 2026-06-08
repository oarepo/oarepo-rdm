#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Inject UI labels for RDM record-level fields into ui_model.

RDMRecordSchemaMixin adds `files`/`access`/`pids` via marshmallow only — they
never reach the YAML-driven ui_model walker, so the UI renders raw paths
like `children.files.children.enabled`. This preset loads `ui_labels.yaml`
and patches the matching labels into `ui_model`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model import from_yaml
from oarepo_model.customizations import AddToDictionary, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMRecordRootLabelsPreset(Preset):
    """Patch UI labels for RDM record-level fields into ui_model.

    The YAML's per-node shape (label/hint/help/children) already matches the
    ui_model node shape, so we patch it straight in under `children`.
    """

    modifies = ("ui_model",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddToDictionary(
            "ui_model",
            {"children": from_yaml("ui_labels.yaml", __file__)},
            patch=True,
        )
