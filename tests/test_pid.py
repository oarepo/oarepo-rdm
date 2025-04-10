from invenio_access.permissions import system_identity
from invenio_rdm_records.records.api import RDMDraft
from modelc.proxies import current_service as modelc_service
from modelc.records.api import ModelcDraft


def test_pid(workflow_data, search_clear):
    modelc_record1 = modelc_service.create(
        system_identity,
        {"metadata": {"title": "blah", "cdescription": "kch"}, **workflow_data},
    )
    id_ = modelc_record1["id"]
    draft = RDMDraft.pid.resolve(id_)
    assert isinstance(draft, ModelcDraft)
