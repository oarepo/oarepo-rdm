from invenio_access.permissions import system_identity
from invenio_rdm_records.records.api import RDMDraft
import pytest
from invenio_drafts_resources.records.api import DraftRecordIdProviderV2
from invenio_records.systemfields.base import SystemFieldsExt
from invenio_pidstore.errors import PIDAlreadyExists
from oarepo_runtime.records.pid_providers import UniversalPIDMixin


FAKE_PID = "xavsd-8adfd"


class ModelaFakePIDProvider(UniversalPIDMixin, DraftRecordIdProviderV2):
    pid_type = "modela"

    def generate_id(self, **kwargs):
        return FAKE_PID


class ModelbFakePIDProvider(DraftRecordIdProviderV2):
    pid_type = "modelb"

    def generate_id(self, **kwargs):
        return FAKE_PID


class ModelcFakePIDProvider(UniversalPIDMixin, DraftRecordIdProviderV2):
    pid_type = "modelc"

    def generate_id(self, **kwargs):
        return FAKE_PID

def test_pid(model_c, workflow_data, search_clear):
    modelc_record1 = model_c.RecordService.create(
        system_identity,
        {"metadata": {"title": "blah", "cdescription": "kch"}, **workflow_data},
    )
    id_ = modelc_record1["id"]
    draft = RDMDraft.pid.resolve(id_)
    assert isinstance(draft, model_c.Draft)

def monkeypatch_pid_provider(cls, provider, monkeypatch):
    monkeypatch.setattr(cls.pid.field, "_provider", provider)
    for extension in cls._extensions:
        if isinstance(extension, SystemFieldsExt):
            monkeypatch.setattr(extension.declared_fields["pid"], "_provider", provider)


def test_universal_provider(model_a, model_b, model_c, rdm_records_service, identity_simple, workflow_data, monkeypatch, search_clear):
    recorda = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modela-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    recordb = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modelb-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )

    monkeypatch_pid_provider(model_a.Draft, ModelaFakePIDProvider, monkeypatch)
    monkeypatch_pid_provider(model_b.Draft, ModelbFakePIDProvider, monkeypatch)
    monkeypatch_pid_provider(model_c.Draft, ModelcFakePIDProvider, monkeypatch)

    recorda = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modela-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    # record does not use collective check
    recordb = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modelb-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    assert recorda["id"] == recordb["id"]
    with pytest.raises(PIDAlreadyExists):
        rdm_records_service.create(
            identity_simple, data={"$schema": "local://modelc-1.0.0.json", **workflow_data, "files": {"enabled": False}}
        )
