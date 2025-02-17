import pytest
from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError
from modelc.proxies import current_service as modelc_service

def test_read(
        rdm_records_service, identity_simple, search_clear
):
    sample_draft = modelc_service.create( # todo - use pytest-oarepo? needs to implement the option for multiple models
        identity_simple,
        {"metadata": {"title": "blah", "cdescription": "kch"}},
    )
    with pytest.raises(PIDDoesNotExistError):
        rdm_records_service.read_draft(identity_simple, "nonsense")
    read_record = rdm_records_service.read_draft(identity_simple, sample_draft["id"])
    assert read_record.data["$schema"] == "local://modelc-1.0.0.json"


def test_update(
        rdm_records_service, identity_simple, search_clear
):
    sample_draft = modelc_service.create(
        identity_simple,
        {"metadata": {"title": "blah", "cdescription": "kch"}},
    )

    with pytest.raises(PIDDoesNotExistError):
        rdm_records_service.update_draft(
            identity_simple, "nonsense", {"metadata": {"title": "blah", "cdescription": "lalala"}}
        )

    old_record_data = rdm_records_service.read_draft(
        identity_simple, sample_draft["id"]
    ).data
    updated_record = rdm_records_service.update_draft(
        identity_simple, sample_draft["id"], {"metadata": {"title": "blah", "cdescription": "lalala"}}
    )
    updated_record_read = rdm_records_service.read_draft(identity_simple, sample_draft["id"])
    assert old_record_data["metadata"] == sample_draft["metadata"]
    assert (
        updated_record.data["metadata"]
        == {"title": "blah", "cdescription": "lalala"}
        != old_record_data["metadata"]
    )
    assert updated_record_read.data["metadata"] == updated_record.data["metadata"]
    assert (
        updated_record.data["revision_id"]
        == updated_record_read.data["revision_id"]
        == old_record_data["revision_id"] + 1
    )


def test_delete(rdm_records_service, identity_simple, search_clear):

    sample_draft = modelc_service.create(
        identity_simple,
        {"metadata": {"title": "blah", "cdescription": "kch"}},
    )

    with pytest.raises(PIDDoesNotExistError):
        rdm_records_service.delete_draft(identity_simple, "nonsense")

    to_delete_record = rdm_records_service.read_draft(identity_simple, sample_draft["id"])
    assert to_delete_record
    rdm_records_service.delete_draft(identity_simple, sample_draft["id"])
    with pytest.raises(PIDDoesNotExistError):
        rdm_records_service.read_draft(identity_simple, sample_draft["id"])

def test_publish(rdm_records_service, identity_simple, search_clear):

    sample_draft = modelc_service.create(
        identity_simple,
        {"metadata": {"title": "blah", "cdescription": "kch"}, "files": {"enabled": False}}
    )

    publish = rdm_records_service.publish(identity_simple, sample_draft["id"])
    record = rdm_records_service.read(identity_simple, sample_draft["id"])



"""
def test_create(app, db, record_service, sample_metadata_list, search_clear):
    created_records = []
    for sample_metadata_point in sample_metadata_list:
        created_records.append(
            record_service.create(system_identity, sample_metadata_point)
        )
    for sample_metadata_point, created_record in zip(
        sample_metadata_list, created_records
    ):
        created_record_reread = record_service.read_draft(
            system_identity, created_record["id"]
        )
        assert (
            created_record_reread.data["metadata"] == sample_metadata_point["metadata"]
        )
"""
