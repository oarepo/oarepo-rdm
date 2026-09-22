# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""UI overrides for invenio-app-rdm."""

from __future__ import annotations

from .config import RDMRecordsUIResourceConfig
from .resource import RDMRecordsUIResource

__all__ = ["RDMRecordsUIResource", "RDMRecordsUIResourceConfig"]
