from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service
from modelc.proxies import current_service as modelc_service
from modelc.records.api import ModelcDraft


def test_description_search(
    app, db, search_clear, custom_fields, workflow_data, identity_simple
):
    modelc_record0 = modelc_service.create(
        system_identity,
        {"metadata": {"title": "blah", "cdescription": "bbb"}, **workflow_data},
    )
    modelc_record1 = modelc_service.create(
        identity_simple,
        {"metadata": {"title": "blah", "cdescription": "kch"}, **workflow_data},
    )
    modelc_record2 = modelc_service.create(
        identity_simple,
        {"metadata": {"title": "aaaaa", "cdescription": "jej"}, **workflow_data},
    )
    ModelcDraft.index.refresh()

    result = current_rdm_records_service.search_drafts(
        system_identity,
        {"q": "jej", "sort": "bestmatch", "page": 1, "size": 10, "facets": {}},
    )
    results = result.to_dict()
    assert len(results["hits"]["hits"]) == 1

    rec_id = modelc_record2.data["id"]
    assert rec_id == results["hits"]["hits"][0]["id"]
    assert (
        results["links"]["self"]
        == "http://localhost/user/search?page=1&q=jej&size=10&sort=bestmatch"
    )
    assert (
        results["hits"]["hits"][0]["links"]["self"]
        == f"http://localhost/modelc/{rec_id}/draft"
    )
