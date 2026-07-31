#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for oarepo_rdm.ext.finalize_app.

Exercises the finalize_app hook that runs at app boot — we assert that the
patch to DraftStatus.review_to_draft_statuses (adding 'cancelled' status)
has been applied.
"""

from __future__ import annotations

from invenio_rdm_records.records.systemfields import DraftStatus


def test_cancelled_status_in_review_to_draft_statuses(app):
    """finalize_app patches review_to_draft_statuses to include 'cancelled'."""
    assert "cancelled" in DraftStatus.review_to_draft_statuses
    assert DraftStatus.review_to_draft_statuses["cancelled"] == "cancelled"
