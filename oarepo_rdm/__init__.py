#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""OARepo extensions for invenio-rdm-records and invenio-app-rdm."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .model.presets import rdm_basic_preset, rdm_complete_preset, rdm_minimal_preset

try:
    __version__ = version("oarepo-rdm")
except PackageNotFoundError:
    __version__ = "0.0.0dev0+unknown"

__all__ = (
    "__version__",
    "rdm_basic_preset",
    "rdm_complete_preset",
    "rdm_minimal_preset",
)
