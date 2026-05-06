#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from io import BytesIO

from .models import modela, modelb, modelc

modela_service = modela.proxies.current_service
modelb_service = modelb.proxies.current_service
modelc_service = modelc.proxies.current_service


def test_empty_list(db, rdm_records_service, users, logged_client, search_clear):
    user = users[0]
    client = logged_client(user)

    # test if empty list is serialized correctly
    result = client.get("/records", headers={"Accept": "application/test+json"})
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

    result = client.get("/records", headers={"Accept": "application/test+json"})
    assert result.status_code == 200
    assert len(result.json["hits"]["hits"]) == 1
    assert "test-ok" in result.json["hits"]
    assert "test-a-ok" in result.json["hits"]["hits"][0]


def test_list_with_model_a_and_b(
    db, rdm_records_service, users, logged_client, vocab_fixtures, required_rdm_metadata, search_clear
):
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
            "metadata": required_rdm_metadata,
            "files": {"enabled": False},
        },
    )
    _publish = rdm_records_service.publish(user.identity, sample_draft_b["id"])

    modelb_service.indexer.refresh()
    modelb_service.draft_indexer.refresh()

    result = client.get("/records", headers={"Accept": "application/test+json"})
    assert result.status_code == 200
    assert len(result.json["hits"]["hits"]) == 2
    assert "test-ok" in result.json["hits"]
    md = {}
    for hit in result.json["hits"]["hits"]:
        md.update(hit)
    assert "test-a-ok" in md
    assert "test-b-ok" in md


def test_list_with_model_a_and_b_and_c(
    db,
    rdm_records_service,
    users,
    logged_client,
    vocab_fixtures,
    required_rdm_metadata,
    search_clear,
):
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
            "metadata": required_rdm_metadata,
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
            "metadata": required_rdm_metadata,
        },
    )
    _publish = rdm_records_service.publish(user.identity, sample_draft_c["id"])
    modelc_service.indexer.refresh()
    modelc_service.draft_indexer.refresh()

    result = client.get("/records", headers={"Accept": "application/test+json"})
    assert result.status_code == 200
    assert len(result.json["hits"]["hits"]) == 2
    assert "test-ok" in result.json["hits"]
    md = {}
    for hit in result.json["hits"]["hits"]:
        md.update(hit)
    assert "test-a-ok" in md
    assert "test-b-ok" in md


def test_read(
    rdm_records_service,
    users,
    client,
    vocab_fixtures,
    required_rdm_metadata,
    link2testclient,
    search_clear,
):
    user = users[0]

    sample = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modelc-v1.0.0.json",
            "files": {"enabled": False},
            "metadata": {
                **required_rdm_metadata,
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

    result = client.get(f"/records/{sample['id']}")
    assert result.status_code == 200
    assert result.json["links"] != {}

    # 1. get UI representation from the self url
    result = client.get(
        link2testclient(result.json["links"]["self"]),
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

    # 2. get UI representation from the /records url

    result = client.get(
        f"/records/{sample['id']}",
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


def _upload_file_via_resource(client, sample, link2testclient, link="files") -> None:
    init = client.post(
        link2testclient(sample["links"][link]),
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
        json=[
            {"key": "test.pdf", "metadata": {"title": "Test file"}},
        ],
    )
    client.put(
        link2testclient(init.json["entries"][0]["links"]["content"]),
        headers={
            "content-type": "application/octet-stream",
            "Accept": "application/vnd.inveniordm.v1+json",
        },
        data=BytesIO(b"testfile"),
    )
    client.post(
        link2testclient(init.json["entries"][0]["links"]["commit"]),
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )


def test_draft_file_ui_serialization(
    rdm_records_service, users, logged_client, link2testclient, location, search_clear
):
    user = users[0]
    client = logged_client(user)

    resp = client.post(
        "/records",
        json={
            "$schema": "local://modela-v1.0.0.json",
            "files": {"enabled": True},
            "metadata": {"title": "Test record"},
        },
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )
    assert resp.status_code == 201
    sample_draft = resp.json
    _upload_file_via_resource(client, sample_draft, link2testclient)
    file_resp = client.get(
        link2testclient(sample_draft["links"]["files"]),
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )
    assert file_resp.status_code == 200
    assert "entries" in file_resp.json
    assert len(file_resp.json["entries"]) == 1


def test_file_ui_serialization(rdm_records_service, users, logged_client, link2testclient, location, search_clear):
    user = users[0]
    client = logged_client(user)

    resp = client.post(
        "/records",
        json={
            "$schema": "local://modela-v1.0.0.json",
            "files": {"enabled": True},
            "metadata": {"title": "Test record"},
        },
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )
    sample_draft = resp.json
    _upload_file_via_resource(client, sample_draft, link2testclient)
    publish_resp = client.post(
        link2testclient(sample_draft["links"]["publish"]),
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )
    assert publish_resp.status_code == 202
    published = publish_resp.json
    file_resp = client.get(
        link2testclient(published["links"]["files"]),
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )
    assert file_resp.status_code == 200
    assert "entries" in file_resp.json
    assert len(file_resp.json["entries"]) == 1


def test_ui_list_serializer_per_model(
    db,
    rdm_records_service,
    users,
    logged_client,
    vocab_fixtures,
    required_rdm_metadata,
    search_clear,
):
    """Regression: /records with UI mimetype must delegate to each model's own serializer.

    Before ff9623b, DelegatedSerializer.serialize_object_list compared serializers
    by type() instead of identity.  Every model's UI serializer is a distinct
    MarshmallowSerializer instance of the same class, so the old check treated them
    as identical and used only the first one for all hits.

    modelc (rdm_complete_preset) includes UIRecordSchema which produces ui.creators
    with an affiliations index.  modela (rdm_minimal_preset) does not.
    If the wrong serializer is used for modelc's hit, ui.creators will be missing.
    """
    user = users[0]
    client = logged_client(user)

    # modela — minimal preset, no creators UI processing
    sample_draft_a = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modela-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(user.identity, sample_draft_a["id"])
    modela_service.indexer.refresh()
    modela_service.draft_indexer.refresh()

    # modelc — complete preset with creators, processed by UIRecordSchema
    sample_draft_c = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modelc-v1.0.0.json",
            "files": {"enabled": False},
            "metadata": required_rdm_metadata,
        },
    )
    rdm_records_service.publish(user.identity, sample_draft_c["id"])
    modelc_service.indexer.refresh()
    modelc_service.draft_indexer.refresh()

    result = client.get(
        "/records",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    )
    assert result.status_code == 200

    hits = result.json["hits"]["hits"]
    assert len(hits) == 2

    hits_by_schema = {hit["$schema"]: hit for hit in hits}

    # modelc's hit must have ui.creators — only present when the complete-preset
    # UIRecordSchema is used (make_affiliation_index processes creators)
    modelc_hit = hits_by_schema["local://modelc-v1.0.0.json"]
    assert "ui" in modelc_hit
    assert "creators" in modelc_hit["ui"], "modelc hit is missing ui.creators — wrong serializer was likely used"
    assert "creators" in modelc_hit["ui"]["creators"]
    assert "affiliations" in modelc_hit["ui"]["creators"]

    # modela's hit must NOT have ui.creators — minimal preset has no UIRecordSchema mixin
    modela_hit = hits_by_schema["local://modela-v1.0.0.json"]
    assert "ui" in modela_hit
    assert "creators" not in modela_hit["ui"]


def test_undefined_model_error_handler(rdm_records_service, users, logged_client, search_clear):
    user = users[0]
    client = logged_client(user)

    sample_draft = client.post(
        "/records",
        json={
            "$schema": "local://idontexist-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    assert sample_draft.status_code == 400
    assert sample_draft.json["message"] == "Model for schema local://idontexist-v1.0.0.json does not exist."
