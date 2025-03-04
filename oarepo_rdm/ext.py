#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""OARepo-Requests extension."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invenio_base.utils import obj_or_import_string
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_rdm_records.resources import RDMRecordFilesResourceConfig, RDMDraftFilesResourceConfig
from invenio_rdm_records.services import (
    RDMFileDraftServiceConfig,
    RDMFileRecordServiceConfig, RecordAccessService,
)
from invenio_rdm_records.services.files.service import RDMFileService
from invenio_rdm_records.services.pids.manager import PIDManager
from invenio_rdm_records.services.pids.service import PIDsService
from invenio_records_resources.records.systemfields import IndexField
from invenio_records_resources.records.systemfields.pid import PIDField
from invenio_records_resources.resources.files.resource import FileResource


from oarepo_global_search.proxies import current_global_search
from oarepo_runtime.datastreams.utils import get_record_service_for_record_class

from oarepo_rdm import config
from oarepo_rdm.records.systemfields.pid import (
    OARepoDraftPIDFieldContext,
    OARepoPIDFieldContext,
)
from oarepo_rdm.resources.config import OARepoRDMRecordResourceConfig
from oarepo_rdm.resources.resources import OARepoRDMRecordResource
from oarepo_rdm.services.access.service import OARepoRecordAccessService
from oarepo_rdm.services.config import OARepoRDMServiceConfig
from oarepo_rdm.services.service import OARepoRDMService
from invenio_requests.proxies import current_requests

if TYPE_CHECKING:
    from flask import Flask


class OARepoRDM(object):
    """OARepo extension of Invenio-Vocabularies."""

    def __init__(self, app: Flask = None) -> None:
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        self.app = app
        self.init_config(app)
        app.extensions["oarepo-rdm"] = self

    def init_config(self, app):
        requests_registered_resolvers = app.config.setdefault(
            "REQUESTS_REGISTERED_RESOLVERS", []
        )
        for event_type in config.REQUESTS_REGISTERED_RESOLVERS:
            if event_type not in requests_registered_resolvers:
                requests_registered_resolvers.append(event_type)

    def record_cls_from_pid_type(self, pid_type, is_draft: bool):
        for model in self.app.config["GLOBAL_SEARCH_MODELS"]:
            service_cfg = obj_or_import_string(model["service_config"])

            if is_draft:
                draft_cls = getattr(service_cfg, "draft_cls", None)
                if draft_cls:
                    provider = draft_cls.pid.field._provider
                    if provider.pid_type == pid_type:
                        return draft_cls
            else:
                record_cls = getattr(service_cfg, "record_cls", None)
                if record_cls:
                    provider = record_cls.pid.field._provider
                    if provider.pid_type == pid_type:
                        return record_cls

    def get_pid_type_from_pid(self, pid_value):
        pids = PersistentIdentifier.query.filter_by(pid_value=pid_value).all()
        if not pids:
            raise PIDDoesNotExistError("", pid_value)
        if len(pids) > 1:
            raise ValueError("Multiple PIDs found")
        return pids[0].pid_type

    def record_service_from_pid_type(
        self, pid_type, is_draft: bool = False
    ):  # there isn't specialized draft service for now
        record_cls = self.record_cls_from_pid_type(pid_type, is_draft)
        return get_record_service_for_record_class(record_cls)


def _service_configs(app):
    """Customized service configs."""

    class ServiceConfigs:
        record = OARepoRDMServiceConfig.build(app)
        file = RDMFileRecordServiceConfig.build(app)
        file_draft = RDMFileDraftServiceConfig.build(app)

    return ServiceConfigs


def api_finalize_app(app: Flask) -> None:
    """Finalize app."""
    finalize_app(app)


def finalize_app(app: Flask) -> None:
    """Finalize app."""
    rdm = app.extensions["invenio-rdm-records"]
    from invenio_rdm_records.records.api import RDMDraft, RDMRecord
    service_configs = _service_configs(app)
    oarepo_service = OARepoRDMService(
        service_configs.record,
        files_service=RDMFileService(service_configs.file),
        draft_files_service=RDMFileService(service_configs.file_draft),
        access_service=OARepoRecordAccessService(service_configs.record),
        pids_service=PIDsService(service_configs.record, PIDManager),
        # review_service=ReviewService(service_configs.record),
    )
    RDMRecord.pid = PIDField(context_cls=OARepoPIDFieldContext)
    RDMDraft.pid = PIDField(context_cls=OARepoDraftPIDFieldContext)
    RDMRecord.index = IndexField(None, search_alias=current_global_search.indices)
    RDMDraft.index = IndexField(None, search_alias=current_global_search.indices)
    rdm.records_service = oarepo_service


    rdm.records_resource = OARepoRDMRecordResource(
        service=oarepo_service,
        config=OARepoRDMRecordResourceConfig.build(app),
    )
    # Record files resource
    rdm.record_files_resource = FileResource(
        service=rdm.records_service.files,
        config=RDMRecordFilesResourceConfig.build(app),
    )
    # Draft files resource
    rdm.draft_files_resource = FileResource(
        service=rdm.records_service.draft_files,
        config=RDMDraftFilesResourceConfig.build(app),
    )

    for type in app.config["REQUESTS_REGISTERED_RESOLVERS"]:
        current_requests.entity_resolvers_registry.register_type(type)


    sregistry = app.extensions["invenio-records-resources"].registry
    sregistry.register(rdm.records_service, service_id="records")
    sregistry.register(rdm.records_service.files, service_id="files")
    sregistry.register(rdm.records_service.draft_files, service_id="draft-files")
