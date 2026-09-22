# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Various errors."""

from __future__ import annotations


class UndefinedModelError(ValueError):
    """Error raised when model can not be found."""
