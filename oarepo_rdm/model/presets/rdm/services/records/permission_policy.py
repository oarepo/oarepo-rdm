# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate permission policy class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services.permissions import RDMRecordPermissionPolicy
from invenio_records_permissions.policies.records import RecordPermissionPolicy
from oarepo_model.customizations import Customization, ReplaceBaseClass
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMPermissionPolicyPreset(Preset):
    """Preset for record service class."""

    modifies = ("PermissionPolicy",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ReplaceBaseClass(
            "PermissionPolicy",
            RecordPermissionPolicy,
            RDMRecordPermissionPolicy,
            subclass=True,
        )
