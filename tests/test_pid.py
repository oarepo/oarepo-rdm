from invenio_access.permissions import system_identity
from invenio_rdm_records.records.api import RDMDraft
from modelc.proxies import current_service as modelc_service
from modelc.records.api import ModelcDraft

from modela.records.api import ModelaIdProvider, ModelaDraft
from modelb.records.api import ModelbIdProvider, ModelbDraft
from invenio_records_resources.records.systemfields.pid import PIDField, PIDFieldContext

FAKE_PID = "xavsd-8adfd"
class ModelaFakePIDProvider(ModelaIdProvider):
    def generate_id(self, record, **kwargs):
        return FAKE_PID

class ModelbFakePIDProvider(ModelbIdProvider):
    def generate_id(self, record, **kwargs):
        return FAKE_PID


def test_pid(workflow_data, search_clear):
    modelc_record1 = modelc_service.create(
        system_identity,
        {"metadata": {"title": "blah", "cdescription": "kch"}, **workflow_data},
    )
    id_ = modelc_record1["id"]
    draft = RDMDraft.pid.resolve(id_)
    assert isinstance(draft, ModelcDraft)

def test_collective_provider(rdm_records_service, identity_simple, workflow_data, search_clear):

    # should work normally
    recorda = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modela-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    recordb = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modelb-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )

    ModelaDraft.pid = PIDField(
        provider=ModelaFakePIDProvider,
        context_cls=PIDFieldContext,
        create=True,
        delete=False,
    )
    ModelbDraft.pid = PIDField(
        provider=ModelbFakePIDProvider,
        context_cls=PIDFieldContext,
        create=True,
        delete=False,
    )
    # the second should crash on the collective pid
    recorda = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modela-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    recordb = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modelb-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )


    """
    recordc = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modelc-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    recorda = rdm_records_service.publish(identity_simple, recorda["id"])
    recordb = rdm_records_service.publish(identity_simple, recordb["id"])
    recordc = rdm_records_service.publish(identity_simple, recordc["id"])
    """
