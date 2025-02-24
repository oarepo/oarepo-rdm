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

from invenio_records_resources.records.systemfields import IndexField

from oarepo_rdm.records.systemfields.pid import OARepoPIDFieldContext, OARepoDraftPIDFieldContext
from oarepo_rdm.services.config import OARepoRDMServiceConfig
from oarepo_rdm.services.service import OARepoRDMService
from invenio_rdm_records.services import (
    CommunityRecordsService,
    IIIFService,
    RDMCommunityRecordsConfig,
    RDMFileDraftServiceConfig,
    RDMFileRecordServiceConfig,
    RDMRecordCommunitiesConfig,
    RDMRecordRequestsConfig,
    RDMRecordService,
    RDMRecordServiceConfig,
    RecordAccessService,
    RecordRequestsService,
)
from invenio_rdm_records.services.files.service import RDMFileService
from invenio_rdm_records.services.review.service import ReviewService
from invenio_rdm_records.services.pids.service import PIDsService
from invenio_rdm_records.services.pids.manager import PIDManager
from oarepo_global_search.proxies import current_global_search_service
from invenio_base.utils import obj_or_import_string
from oarepo_runtime.datastreams.utils import get_record_service_for_record_class

from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.resolver import Resolver
from invenio_records.systemfields import (
    ModelField,
    RelatedModelField,
    RelatedModelFieldContext,
)
from invenio_records_resources.records.systemfields.pid import PIDFieldContext, PIDField
from sqlalchemy import inspect
from oarepo_communities.utils import get_service_from_schema_type
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.errors import PIDDoesNotExistError
from oarepo_global_search.proxies import current_global_search

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
        app.extensions["oarepo-rdm"] = self

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
        if len(pids)>1:
            raise ValueError("Multiple PIDs found")
        return pids[0].pid_type

    def record_service_from_pid_type(self, pid_type, is_draft: bool = False): # there isn't specialized draft service for now
        record_cls = self.record_cls_from_pid_type(pid_type, is_draft)
        return get_record_service_for_record_class(record_cls)


def _service_configs(app):
    """Customized service configs."""

    class ServiceConfigs:
        record = OARepoRDMServiceConfig()
        file = RDMFileRecordServiceConfig.build(app)
        file_draft = RDMFileDraftServiceConfig.build(app)
        record_communities = RDMRecordCommunitiesConfig.build(app)
        community_records = RDMCommunityRecordsConfig.build(app)
        record_requests = RDMRecordRequestsConfig.build(app)


    return ServiceConfigs

def api_finalize_app(app: Flask) -> None:
    """Finalize app."""
    finalize_app(app)

def finalize_app(app: Flask) -> None:
    """Finalize app."""
    rdm = app.extensions["invenio-rdm-records"]
    from invenio_rdm_records.records.api import RDMRecord, RDMDraft
    from oarepo_rdm.records.systemfields.pid import OARepoPIDField


    service_configs = _service_configs(app)

    oarepo_service = OARepoRDMService(
        service_configs.record,
        files_service=RDMFileService(service_configs.file),
        draft_files_service=RDMFileService(service_configs.file_draft),
        access_service=RecordAccessService(service_configs.record),
        pids_service=PIDsService(service_configs.record, PIDManager),
        review_service=ReviewService(service_configs.record),
    )
    RDMRecord.pid = OARepoPIDField(context_cls=OARepoPIDFieldContext)
    RDMDraft.pid = OARepoPIDField(context_cls=OARepoDraftPIDFieldContext)
    RDMRecord.index = IndexField(current_global_search.indices)
    RDMDraft.index = IndexField(current_global_search.indices)

    rdm.records_service = oarepo_service


    """
    rdm.records_service = OARepoRDMService(OARepoRDMServiceConfig())





    from invenio_requests.proxies import current_event_type_registry

    # Register services - cannot be done in extension because
    # Invenio-Records-Resources might not have been initialized.
    rr_ext = app.extensions["invenio-records-resources"]
    # idx_ext = app.extensions["invenio-indexer"]
    ext = app.extensions["oarepo-requests"]

    # services
    rr_ext.registry.register(
        ext.requests_service,
        service_id=ext.requests_service.config.service_id,
    )

    # todo i have to do this cause there is bug in invenio-requests for events
    # but imo this is better than entrypoints
    for type in app.config["REQUESTS_REGISTERED_EVENT_TYPES"]:
        current_event_type_registry.register_type(type)

    ext.notification_recipients_resolvers_registry = app.config[
        "NOTIFICATION_RECIPIENTS_RESOLVERS"
    ]
    """