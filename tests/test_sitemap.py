# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from oarepo_rdm.sitemap import SitemapSectionOfOARepoRecords

from .models import modela

modela_service = modela.proxies.current_service


def _publish(rdm_records_service, identity, access=None):
    data = {
        "metadata": {"title": "blah", "adescription": "kch"},
        "files": {"enabled": False},
    }
    if access:
        data["access"] = access
    draft = modela_service.create(identity, data)
    return rdm_records_service.publish(identity, draft["id"])


def test_sitemap_is_configured(app):
    """The sitemap lists OARepo records instead of the (unused) stock RDM ones."""
    sections = [type(section).__name__ for section in app.config["SITEMAP_SECTIONS"]]

    assert sections == ["SitemapSectionOfOARepoRecords", "SitemapSectionOfCommunities"]


def test_sitemap_lists_public_published_records(
    app, db, rdm_records_service, identity_simple, vocab_fixtures, search_clear
):
    public = _publish(rdm_records_service, identity_simple)
    restricted = _publish(
        rdm_records_service,
        identity_simple,
        access={"record": "restricted", "files": "restricted"},
    )
    modela_service.create(
        identity_simple,
        {"metadata": {"title": "never published", "adescription": "kch"}, "files": {"enabled": False}},
    )
    modela_service.indexer.refresh()
    modela_service.draft_indexer.refresh()

    section = SitemapSectionOfOARepoRecords()
    entries = [section.to_dict(entity) for entity in section.iter_entities()]

    # only the public published record, linked to the model's own record detail page
    assert len(entries) == 1
    assert entries[0]["loc"].endswith(f"/modela_ui/record_detail/{public['id']}")
    assert restricted["id"] not in entries[0]["loc"]
    # W3C datetime, as required by the sitemap protocol
    assert entries[0]["lastmod"].endswith("Z")
