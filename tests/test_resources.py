from modela.records.api import ModelaDraft, ModelaRecord
from modela.proxies import current_service as modela_service

def test_list(rdm_records_service, users, logged_client, workflow_data, search_clear):
    user = users[0]
    client = logged_client(user)

    sample_draft = rdm_records_service.create(
        user.identity,
        data={"$schema": "local://modela-1.0.0.json", "files": {"enabled": False}, **workflow_data},
    )
    publish = rdm_records_service.publish(user.identity, sample_draft["id"])

    modela_service.indexer.refresh()
    modela_service.draft_indexer.refresh()

    result = client.get("/records")
    assert len(result.json["hits"]["hits"]) == 1

def test_read(rdm_records_service, users, logged_client, workflow_data, search_clear):
    user = users[0]
    client = logged_client(user)


    sample = rdm_records_service.create(
        user.identity,
        data={"$schema": "local://modela-1.0.0.json", "files": {"enabled": False}, **workflow_data},
    )
    publish = rdm_records_service.publish(user.identity, sample["id"])

    result = client.get(f"/records/{sample['id']}")
    assert result.status_code == 200
