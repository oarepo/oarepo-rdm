# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for RDM info component."""

from __future__ import annotations

from oarepo_rdm.info import RDMInfoComponent


def test_info_component(app):
    assert "oarepo_rdm.info:RDMInfoComponent" in app.config["INFO_ENDPOINT_COMPONENTS"]

    c = RDMInfoComponent(None)  # type: ignore[reportArgumentType]
    data = {"links": {}}
    c.repository(data)
    assert "records" in data["links"]
    assert "drafts" in data["links"]
