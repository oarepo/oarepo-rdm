# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for adding resource error handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.resources.config import error_handlers
from oarepo_model.customizations import AddToDictionary, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMErrorHandlersPreset(Preset):
    """Preset for handling errors."""

    modifies = ("record_error_handlers",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        # ``error_handlers`` is keyed by exception classes (``dict[type, Any]``),
        # whereas ``AddToDictionary`` is typed for ``dict[str, Any]``; the exception
        # keys are intended here, so cast to satisfy the checker.
        yield AddToDictionary(
            "record_error_handlers",
            {
                **error_handlers,
            },
        )
