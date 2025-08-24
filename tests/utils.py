#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invenio_records_resources.records.api import Record
    from invenio_records_resources.services.records.results import RecordItem


def record_from_result(result: RecordItem) -> Record:
    """Convert a service result to a record."""
    return result._record  # type: ignore[no-any-return]  # noqa SLF001 access private member
