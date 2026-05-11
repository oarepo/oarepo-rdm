#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for the generic /uploads/new (deposit_create) route in oarepo_rdm.ui.views."""

from __future__ import annotations


def test_deposit_create_requires_login(app, client, extra_entry_points):
    """Test that /uploads/new requires authentication."""
    with client.get("/uploads/new") as resp:
        # Should redirect to login page
        assert resp.status_code == 302
        assert "login" in resp.location.lower()
