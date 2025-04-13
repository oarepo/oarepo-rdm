#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""OARepo-Requests extension."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING

from invenio_base.utils import obj_or_import_string
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from oarepo_runtime.datastreams.utils import get_record_service_for_record_class
from invenio_records_resources.services.base.config import ConfiguratorMixin

if TYPE_CHECKING:
    from flask import Flask

from invenio_records_resources.services.records.service import RecordService #or with drafts? or RDMService? what are the possible use cases?
from invenio_records_resources.services.records.config import RecordServiceConfig

@dataclass
class RDMModel:
    service_id: str
    api_service: RecordService
    api_service_config: RecordServiceConfig
    api_resource: any
    api_resource_config: any
    ui_resource_config: any


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
        if len(pids) > 1:
            raise ValueError("Multiple PIDs found")
        return pids[0].pid_type

    def record_service_from_pid_type(
        self, pid_type, is_draft: bool = False
    ):  # there isn't specialized draft service for now
        record_cls = self.record_cls_from_pid_type(pid_type, is_draft)
        return get_record_service_for_record_class(record_cls)

    def _instantiate_configurator_cls(self, cls_):
        if issubclass(cls_, ConfiguratorMixin):
            return cls_.build(self.app)
        else:
            return cls_()

    @cached_property
    def rdm_models(self):
        models = self.app.config["RDM_MODELS"]
        ret = []
        for model_dict in models:
            ret.append(RDMModel(model_dict["service_id"],
                                obj_or_import_string(model_dict["api_service"]), # from service registry? and from exts for resources? reinitializing might be dangerous one day?
                                self._instantiate_configurator_cls(obj_or_import_string(model_dict["api_service_config"])),
                                obj_or_import_string(model_dict["api_resource"]),
                                self._instantiate_configurator_cls(obj_or_import_string(model_dict["api_resource_config"])),
                                obj_or_import_string(model_dict["ui_resource_config"])()))
        return ret

def api_finalize_app(app: Flask) -> None:
    """Finalize app."""
    finalize_app(app)


def finalize_app(app: Flask) -> None:
    """Finalize app."""
    app.config["RECORDS_REST_ENDPOINTS"] = (
        []
    )  # rule /records/<pid(recid):pid_value> is in race condition with
    # /records/<pid_value> from rdm and PIDConverter in it breaks record resolution due to use recid pid type
