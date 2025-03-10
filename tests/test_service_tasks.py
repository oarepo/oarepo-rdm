from invenio_rdm_records.services.tasks import update_expired_embargos
from modela.proxies import current_service as modela_service
from modelb.proxies import current_service as modelb_service


def test_embargo_lift_without_draft(
    rdm_records_service, embargoed_files_record, search_clear
):
    record = embargoed_files_record(modela_service)
    update_expired_embargos()
    record_lifted = rdm_records_service.record_cls.pid.resolve(record["id"])
    assert record_lifted.access.embargo.active is False
    assert record_lifted.access.protection.files == "public"
    assert record_lifted.access.protection.record == "public"
    assert record_lifted.access.status.value == "metadata-only"


def test_embargo_lift_with_draft(
    rdm_records_service, embargoed_files_record, identity_simple, search_clear
):
    record = embargoed_files_record(modela_service)
    service = rdm_records_service

    # Edit a draft
    ongoing_draft = service.edit(identity=identity_simple, id_=record["id"])
    modela_service.config.draft_cls.index.refresh()

    update_expired_embargos()

    record_lifted = service.record_cls.pid.resolve(record["id"])
    draft_lifted = service.draft_cls.pid.resolve(ongoing_draft["id"])

    assert record_lifted.access.embargo.active is False
    assert record_lifted.access.protection.files == "public"
    assert record_lifted.access.protection.record == "public"

    assert draft_lifted.access.embargo.active is False
    assert draft_lifted.access.protection.files == "public"
    assert draft_lifted.access.protection.record == "public"


def test_embargo_lift_with_updated_draft(
    rdm_records_service, embargoed_files_record, identity_simple, search_clear
):
    record = embargoed_files_record(modela_service)
    service = rdm_records_service

    # This draft simulates an existing one while lifting the record
    draft = service.edit(id_=record["id"], identity=identity_simple).data

    # Change record's title and access field to be restricted
    draft["metadata"]["title"] = "Record modified by the user"
    draft["access"]["status"] = "restricted"
    draft["access"]["embargo"] = dict(active=False, until=None, reason=None)
    # Update the ongoing draft with the new data simulating the user's input
    ongoing_draft = service.update_draft(
        id_=draft["id"], identity=identity_simple, data=draft
    )
    modela_service.config.draft_cls.index.refresh()

    update_expired_embargos()

    record_lifted = service.record_cls.pid.resolve(record["id"])
    draft_lifted = service.draft_cls.pid.resolve(ongoing_draft["id"])

    assert record_lifted.access.embargo.active is False
    assert record_lifted.access.protection.files == "public"
    assert record_lifted.access.protection.record == "public"

    assert draft_lifted.access.embargo.active is False
    assert draft_lifted.access.protection.files == "restricted"
    assert draft_lifted.access.protection.record == "public"


def test_embargo_lift_multiple_models(
    rdm_records_service, embargoed_files_record, search_clear
):
    record1 = embargoed_files_record(modela_service)
    record2 = embargoed_files_record(modelb_service)

    update_expired_embargos()

    record1_lifted = rdm_records_service.record_cls.pid.resolve(record1["id"])
    assert record1_lifted.access.embargo.active is False
    assert record1_lifted.access.protection.files == "public"
    assert record1_lifted.access.protection.record == "public"
    assert record1_lifted.access.status.value == "metadata-only"

    record2_lifted = rdm_records_service.record_cls.pid.resolve(record2["id"])
    assert record2_lifted.access.embargo.active is False
    assert record2_lifted.access.protection.files == "public"
    assert record2_lifted.access.protection.record == "public"
    assert record2_lifted.access.status.value == "metadata-only"
