# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""DataCite rights serialization when a title is missing in the default locale."""

from __future__ import annotations

from datacite import schema43
from lxml import etree

from oarepo_rdm.resources.records.datacite import DataCite43Schema


def test_rights_fallback_to_other_language(app, monkeypatch):
    monkeypatch.setitem(app.config, "BABEL_DEFAULT_LOCALE", "cs")
    obj = {"metadata": {"rights": [{"title": {"en": "Custom"}}, {"title": {}}, {"title": {"cs": "Vlastní"}}]}}

    rights = DataCite43Schema().get_rights(obj)

    assert rights == [{"rights": "Custom"}, {}, {"rights": "Vlastní"}]
    # used to raise TypeError: bad argument type: NoneType(None)
    xml = etree.tostring(schema43.rights(None, rights), encoding="unicode")
    assert ">Custom</rights>" in xml
    assert ">Vlastní</rights>" in xml
