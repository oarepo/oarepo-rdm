from modela.proxies import current_service as modela_service
from modela.records.api import ModelaDraft, ModelaRecord
from modelb.proxies import current_service as modelb_service
from modelb.records.api import ModelbDraft, ModelbRecord


def test_description_search(
    rdm_records_service, identity_simple, workflow_data, search_clear
):
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    modela_record2 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "aaaaa", "adescription": "jej"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "bdescription": "blah"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.publish(identity_simple, modela_record2["id"])
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    ModelaRecord.index.refresh()
    ModelbRecord.index.refresh()
    ModelaDraft.index.refresh()  # needed cause the draft might be still found
    ModelbDraft.index.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "jej", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()
    assert len(results["hits"]["hits"]) == 1
    hit_ids = {r["id"] for r in results["hits"]["hits"]}

    assert (
        modela_record2["id"] in hit_ids
    )  # todo modela_record2.data in results["hits"]["hits"] - those are not the same but that's ok?
    assert modelb_record1["id"] not in hit_ids
    assert modela_record1["id"] not in hit_ids


def test_basic_search(
    rdm_records_service, identity_simple, workflow_data, search_clear
):
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    modela_record2 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "aaaaa", "adescription": "jej"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "bdescription": "blah"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.publish(identity_simple, modela_record2["id"])
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    ModelaRecord.index.refresh()
    ModelbRecord.index.refresh()
    ModelaDraft.index.refresh()  # needed cause the draft might be still found
    ModelbDraft.index.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()

    assert len(results["hits"]["hits"]) == 2

    hit_ids = {r["id"] for r in results["hits"]["hits"]}

    assert modela_record2["id"] not in hit_ids
    assert modelb_record1["id"] in hit_ids
    assert modela_record1["id"] in hit_ids


def test_mixed_with_drafts(
    rdm_records_service, identity_simple, workflow_data, search_clear
):
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    modela_record2 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "aaaaa", "adescription": "jej"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "bdescription": "blah"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.publish(identity_simple, modela_record2["id"])

    ModelaRecord.index.refresh()
    ModelbRecord.index.refresh()
    ModelaDraft.index.refresh()
    ModelbDraft.index.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()

    assert len(results["hits"]["hits"]) == 2

    hit_ids = {r["id"] for r in results["hits"]["hits"]}

    assert modela_record2["id"] not in hit_ids
    assert modelb_record1["id"] in hit_ids
    assert modela_record1["id"] in hit_ids


def test_record_and_edited_draft(
    rdm_records_service, identity_simple, workflow_data, search_clear
):
    # should we find both record and draft?
    # edited draft is not found bc it does not have $schema in opensearch
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.edit(identity_simple, modela_record1["id"])

    ModelaRecord.index.refresh()
    ModelbRecord.index.refresh()
    ModelaDraft.index.refresh()  # needed cause the draft might be still found
    ModelbDraft.index.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()

    assert len(results["hits"]["hits"]) == 1

    hit_ids = {r["id"] for r in results["hits"]["hits"]}

    assert modela_record1["id"] in hit_ids


def test_links(rdm_records_service, identity_simple, workflow_data, search_clear):
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "bdescription": "blah"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    ModelbRecord.index.refresh()
    ModelbDraft.index.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 1, "size": 20, "facets": {}},
    )
    results = result.to_dict()

    assert (
        results["links"]["self"]
        == "http://localhost/search?page=1&q=blah&size=20&sort=bestmatch"
    )
    assert results["hits"]["hits"][0]["links"]["self"].startswith(
        "http://localhost/modelb/"
    )


def test_second_page(rdm_records_service, identity_simple, workflow_data, search_clear):
    for r in range(10):
        draft = modelb_service.create(
            identity_simple,
            {
                "metadata": {"title": f"blah {r}", "bdescription": "blah"},
                **workflow_data,
                "files": {"enabled": False},
            },
        )
        rdm_records_service.publish(identity_simple, draft["id"])
    ModelbRecord.index.refresh()
    ModelbDraft.index.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 1, "size": 5, "facets": {}},
    )
    results = result.to_dict()

    assert (
        results["links"]["self"]
        == "http://localhost/search?page=1&q=blah&size=5&sort=bestmatch"
    )
    assert (
        results["links"]["next"]
        == "http://localhost/search?page=2&q=blah&size=5&sort=bestmatch"
    )

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 2, "size": 5, "facets": {}},
    )
    results = result.to_dict()

    assert (
        results["links"]["self"]
        == "http://localhost/search?page=2&q=blah&size=5&sort=bestmatch"
    )
    assert (
        results["links"]["prev"]
        == "http://localhost/search?page=1&q=blah&size=5&sort=bestmatch"
    )


def test_zero_hits(rdm_records_service, identity_simple, workflow_data, search_clear):
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    modela_record2 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "aaaaa", "adescription": "blah"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "bdescription": "blah"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.publish(identity_simple, modela_record2["id"])
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    ModelaRecord.index.refresh()
    ModelbRecord.index.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "jej", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()

    assert len(results["hits"]["hits"]) == 0


def test_multiple_from_one_schema(
    rdm_records_service, identity_simple, workflow_data, search_clear
):
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "kch"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    modela_record2 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "aaaaa", "adescription": "blah"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "kkkkkkkkk", "bdescription": "kkkkk"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.publish(identity_simple, modela_record2["id"])
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    ModelaRecord.index.refresh()
    ModelbRecord.index.refresh()
    ModelaDraft.index.refresh()  # needed cause the draft might be still found
    ModelbDraft.index.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {"q": "blah", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()
    hit_ids = {r["id"] for r in results["hits"]["hits"]}

    assert len(results["hits"]["hits"]) == 2
    assert modelb_record1["id"] not in hit_ids


def test_facets(rdm_records_service, identity_simple, workflow_data, search_clear):
    modela_record1 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "blah", "adescription": "1"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    modela_record2 = modela_service.create(
        identity_simple,
        {
            "metadata": {"title": "aaaaa", "adescription": "2"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    modelb_record1 = modelb_service.create(
        identity_simple,
        {
            "metadata": {"title": "kkkkkkkkk", "bdescription": "3"},
            **workflow_data,
            "files": {"enabled": False},
        },
    )
    rdm_records_service.publish(identity_simple, modela_record1["id"])
    rdm_records_service.publish(identity_simple, modela_record2["id"])
    rdm_records_service.publish(identity_simple, modelb_record1["id"])

    ModelaRecord.index.refresh()
    ModelbRecord.index.refresh()
    ModelaDraft.index.refresh()  # needed cause the draft might be still found
    ModelbDraft.index.refresh()

    result = rdm_records_service.search(
        identity_simple,
        {
            "q": "",
            "sort": "bestmatch",
            "page": 1,
            "size": 10,
            "facets": {"metadata_adescription": ["2"]},
        },
    )
    results = result.to_dict()
    assert len(results["hits"]["hits"]) == 1
    hit_ids = {r["id"] for r in results["hits"]["hits"]}
    assert modela_record2["id"] in hit_ids
