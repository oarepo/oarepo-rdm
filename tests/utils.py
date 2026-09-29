# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invenio_records_resources.records.api import Record
    from invenio_records_resources.services.records.results import RecordItem


def record_from_result(result: RecordItem) -> Record:
    """Convert a service result to a record."""
    return result._record  # type: ignore[no-any-return]  # noqa SLF001 access private member
