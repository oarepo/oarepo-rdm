#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from .models import modela, modelb, modelc

modela_service = modela.proxies.current_service
modelb_service = modelb.proxies.current_service
modelc_service = modelc.proxies.current_service


def test_empty_list(db, rdm_records_service, users, logged_client, search_clear):
    user = users[0]
    client = logged_client(user)

    # test if empty list is serialized correctly
    result = client.get("/api/records", headers={"Accept": "application/test+json"})
    assert result.status_code == 200
    assert len(result.json["hits"]["hits"]) == 0
    assert "test-ok" in result.json["hits"]


def test_list_with_model_a(db, rdm_records_service, users, logged_client, search_clear):
    user = users[0]
    client = logged_client(user)

    sample_draft = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modela-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    _publish = rdm_records_service.publish(user.identity, sample_draft["id"])

    modela_service.indexer.refresh()
    modela_service.draft_indexer.refresh()

    result = client.get("/api/records", headers={"Accept": "application/test+json"})
    assert result.status_code == 200
    assert len(result.json["hits"]["hits"]) == 1
    assert "test-ok" in result.json["hits"]
    assert "test-a-ok" in result.json["hits"]["hits"][0]


def test_list_with_model_a_and_b(db, rdm_records_service, users, logged_client, search_clear):
    user = users[0]
    client = logged_client(user)

    sample_draft = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modela-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    _publish = rdm_records_service.publish(user.identity, sample_draft["id"])

    modela_service.indexer.refresh()
    modela_service.draft_indexer.refresh()

    sample_draft_b = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modelb-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    _publish = rdm_records_service.publish(user.identity, sample_draft_b["id"])

    modelb_service.indexer.refresh()
    modelb_service.draft_indexer.refresh()

    result = client.get("/api/records", headers={"Accept": "application/test+json"})
    assert result.status_code == 200
    assert len(result.json["hits"]["hits"]) == 2
    assert "test-ok" in result.json["hits"]
    md = {}
    for hit in result.json["hits"]["hits"]:
        md.update(hit)
    assert "test-a-ok" in md
    assert "test-b-ok" in md


def test_list_with_model_a_and_b_and_c(db, rdm_records_service, users, logged_client, search_clear):
    # model c does not have test exporter, so it should be skipped in the list
    user = users[0]
    client = logged_client(user)

    sample_draft = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modela-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    _publish = rdm_records_service.publish(user.identity, sample_draft["id"])

    modela_service.indexer.refresh()
    modela_service.draft_indexer.refresh()

    sample_draft_b = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modelb-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    _publish = rdm_records_service.publish(user.identity, sample_draft_b["id"])

    modelb_service.indexer.refresh()
    modelb_service.draft_indexer.refresh()

    sample_draft_c = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modelc-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    _publish = rdm_records_service.publish(user.identity, sample_draft_c["id"])
    modelc_service.indexer.refresh()
    modelc_service.draft_indexer.refresh()

    result = client.get("/api/records", headers={"Accept": "application/test+json"})
    assert result.status_code == 200
    assert len(result.json["hits"]["hits"]) == 2
    assert "test-ok" in result.json["hits"]
    md = {}
    for hit in result.json["hits"]["hits"]:
        md.update(hit)
    assert "test-a-ok" in md
    assert "test-b-ok" in md


def test_read(rdm_records_service, users, client, search_clear, contributor_role_editor):
    user = users[0]

    sample = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modelc-v1.0.0.json",
            "files": {"enabled": False},
            "metadata": {
                "creators": [
                    {
                        "person_or_org": {
                            "type": "personal",
                            "name": "Böhm, Johannes",
                            "given_name": "Johannes",
                            "family_name": "Böhm",
                            "identifiers": [{"identifier": "0000-0002-1208-5473", "scheme": "orcid"}],
                        },
                        "affiliations": [{"name": "Technische Universität Wien"}],
                        "title": "Blah",
                    }
                ],
                "contributors": [
                    {
                        "person_or_org": {
                            "type": "personal",
                            "name": "Böhm, Johannes",
                            "given_name": "Johannes",
                            "family_name": "Böhm",
                            "identifiers": [{"identifier": "0000-0002-1208-5473", "scheme": "orcid"}],
                        },
                        "affiliations": [{"name": "Technische Universität Wien"}],
                        "title": "Blah",
                        "role": {"id": "editor", "title": "Editor"},
                    }
                ],
            },
        },
    )
    _publish = rdm_records_service.publish(user.identity, sample["id"])

    result = client.get(f"/api/records/{sample['id']}")
    assert result.status_code == 200
    assert result.json["links"] != {}

    # 1. get UI representation from the self url
    result = client.get(
        result.json["links"]["self"].replace("http://localhost/", "/api/"),
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )
    assert result.status_code == 200
    ui = result.json["ui"]
    assert ui["creators"] == {
        "creators": [
            {
                "person_or_org": {
                    "type": "personal",
                    "name": "Böhm, Johannes",
                    "given_name": "Johannes",
                    "family_name": "Böhm",
                    "identifiers": [{"identifier": "0000-0002-1208-5473", "scheme": "orcid"}],
                },
                "affiliations": [[1, "Technische Universität Wien"]],
            }
        ],
        "affiliations": [[1, "Technische Universität Wien", None]],
    }
    assert ui["contributors"] == {
        "contributors": [
            {
                "person_or_org": {
                    "type": "personal",
                    "name": "Böhm, Johannes",
                    "given_name": "Johannes",
                    "family_name": "Böhm",
                    "identifiers": [{"identifier": "0000-0002-1208-5473", "scheme": "orcid"}],
                },
                "affiliations": [[1, "Technische Universität Wien"]],
                "role": {"id": "editor", "title": "Editor"},
            }
        ],
        "affiliations": [[1, "Technische Universität Wien", None]],
    }

    # 2. get UI representation from the /api/records url

    result = client.get(
        f"/api/records/{sample['id']}",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )
    assert result.status_code == 200
    ui = result.json["ui"]
    assert ui["creators"] == {
        "creators": [
            {
                "person_or_org": {
                    "type": "personal",
                    "name": "Böhm, Johannes",
                    "given_name": "Johannes",
                    "family_name": "Böhm",
                    "identifiers": [{"identifier": "0000-0002-1208-5473", "scheme": "orcid"}],
                },
                "affiliations": [[1, "Technische Universität Wien"]],
            }
        ],
        "affiliations": [[1, "Technische Universität Wien", None]],
    }
    assert ui["contributors"] == {
        "contributors": [
            {
                "person_or_org": {
                    "type": "personal",
                    "name": "Böhm, Johannes",
                    "given_name": "Johannes",
                    "family_name": "Böhm",
                    "identifiers": [{"identifier": "0000-0002-1208-5473", "scheme": "orcid"}],
                },
                "affiliations": [[1, "Technische Universität Wien"]],
                "role": {"id": "editor", "title": "Editor"},
            }
        ],
        "affiliations": [[1, "Technische Universität Wien", None]],
    }
