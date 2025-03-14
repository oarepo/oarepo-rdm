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
from invenio_requests.proxies import current_requests
from oarepo_runtime.datastreams.utils import get_record_service_for_record_class

from oarepo_rdm import config

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


def api_finalize_app(app: Flask) -> None:
    """Finalize app."""
    finalize_app(app)


def finalize_app(app: Flask) -> None:
    """Finalize app."""

    app.config["RECORDS_REST_ENDPOINTS"] = []  # rule /records/<pid(recid):pid_value> is in race condition with
    #/records/<pid_value> from rdm and PIDConverter in it breaks record resolution due to use recid pid type
    app.config["APP_RDM_ROUTES"] = {
        "record_detail": "/records/<pid_value>",
        "record_file_download": "/records/<pid_value>/files/<path:filename>",
    }

    for type in app.config["REQUESTS_REGISTERED_RESOLVERS"]:
        current_requests.entity_resolvers_registry.register_type(type)
