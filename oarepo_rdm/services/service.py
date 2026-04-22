#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""RDM service extension to use specialized records instead of generic RDM records."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast, override

from flask import current_app
from invenio_db.uow import UnitOfWork, unit_of_work
from invenio_rdm_records.services.services import RDMRecordService
from invenio_records_resources.services import Service as InvenioService
from oarepo_runtime.proxies import current_runtime
from werkzeug.exceptions import Forbidden

from oarepo_rdm.errors import UndefinedModelError

from .config import MultiplexingLinks

_T = TypeVar("_T", bound=type)

if TYPE_CHECKING:
    import datetime
    from collections.abc import Callable, Iterable

    from invenio_access.permissions import Identity
    from invenio_records_permissions.policies.base import BasePermissionPolicy
    from invenio_records_resources.services.records.results import (
        RecordItem,
    )
    from invenio_search import RecordsSearchV2
    from oarepo_runtime.api import Model

pass_through = {
    # These methods are from the base Invenio Service class
    "check_permission",
    "permission_policy",
    "result_item",
    "result_list",
    "result_bulk_item",
    "result_bulk_list",
    # RecordIndexerMixin
    "record_to_index",  # return record.index._name if service inherits from RecordIndexerMixin
    # These methods are from the base Invenio records Service class
    "check_revision_id",  # functionally static method
    "create_search",
    "search_request",
    "search",
    "scan",
    "create_or_update_many",  # to do
    "read_all",
    "read_many",
    # DraftsRecordService (invenio_drafts_resources) -> overridden in RDMRecordService
    "search_drafts",
}

pass_through_rdm = {  # RDMRecordService (invenio_rdm_records) — first defined or overridden there
    "cleanup_record",  # not implemented
    "scan_expired_embargos",
    "set_user_quota",
}

delegate_to_specialized_service = {
    # These methods are from the base Invenio drafts Service class
    "delete_draft",
    "edit",
    "exists",
    "import_files",
    "new_version",
    "read_latest",
    "validate_draft",
    # DraftsRecordService -> overridden in RDMRecordService
    "publish",
    "read_draft",
    "search_versions",
    "update_draft",
    # BaseRecordService (invenio_records_resources) -> overridden in RDMRecordService
    "read",
    "update",
    "delete",
}

delegate_to_specialized_service_rdm = {
    "delete_record",
    "lift_embargo",
    "mark_record_for_purge",
    "purge_record",
    "restore_record",
    "scan_versions",
    "set_quota",
    "unmark_record_for_purge",
    "update_tombstone",
    "request_deletion",
    "file_modification",
    "read_revision",
    "search_revisions",
}

permissions_search_mapping = {
    "read": "search",
    "read_deleted": "search",
    "read_draft": "search_drafts",
    "read_all": "search_all",
}


def check_fully_overridden(
    pass_through: Iterable[str],
    delegate_to_specialized: Iterable[str],
    base_class: type,
) -> Callable[[_T], _T]:
    """Check that all methods are fully overridden in the subclass."""

    def wrapper(cls: _T) -> _T:
        # go through base classes and check if methods defined on them are overriden in the class
        for name, value in vars(base_class).items():
            if not callable(value) or name.startswith("_") or name in pass_through or name in delegate_to_specialized:
                continue

            this_class_value = cls.__dict__.get(name, None)
            if this_class_value is value:
                raise TypeError(f"Method with name {value.__qualname__} is not overridden in OARepoRDMService.")
        return cls

    return wrapper


def pass_to_specialized_service(
    method_names: Iterable[str],
) -> Callable[[_T], _T]:
    """Pass the call to the specialized service.

    The service is selected by converting the id to pid type and resolving
    the service by pid type.
    """

    def make_delegate(method_name: str) -> Callable[..., Any]:
        def delegate(self: DelegationToSpecializedServiceMixin, *args: Any, **kwargs: Any) -> Any:
            # might be called with positional arguments (almost always)
            # or with keyword arguments (lift embargoes are called this way)
            if "id_" in kwargs:
                id_ = kwargs["id_"]
            elif "_id" in kwargs:
                # lift_embargo is the only one having it this way
                id_ = kwargs["_id"]
            else:
                # called as (identity, id_)
                id_ = args[1]

            specialized_service = self._get_specialized_service(id_)
            method = getattr(specialized_service, method_name)
            return method(*args, **kwargs)

        return delegate

    def wrapper(cls: _T) -> _T:
        overriden_methods = {}
        for name in method_names:
            if not hasattr(cls, name):
                raise TypeError(f"Method {name} is not implemented in {cls.__name__}")
            overriden_methods[name] = make_delegate(name)
        return type(cls.__name__, (cls,), overriden_methods)  # type: ignore[return-value]

    return wrapper


class DelegationToSpecializedServiceMixin(InvenioService):
    """Mixin for delegating running components and permission checks to specialized model services."""

    attribute_on_base_service: str = ""

    def _get_specialized_service(self, pid_value: str) -> InvenioService:
        """Get a specialized service based on the pid_value of the record."""
        pid_type = current_runtime.find_pid_type_from_pid(pid_value)
        base_service = current_runtime.model_by_pid_type[pid_type].service
        return getattr(base_service, self.attribute_on_base_service) if self.attribute_on_base_service else base_service

    @override
    def run_components(self, action: str, *args: Any, **kwargs: Any) -> None:
        if "record" in kwargs:
            self._get_specialized_service(kwargs["record"].pid.pid_value).run_components(action, *args, **kwargs)
        else:
            super().run_components(action, *args, **kwargs)

    @override
    def permission_policy(self, action_name: str, **kwargs: Any) -> BasePermissionPolicy:
        if "record" in kwargs:
            return self._get_specialized_service(kwargs["record"].pid.pid_value).permission_policy(
                action_name, **kwargs
            )
        return super().permission_policy(action_name, **kwargs)


# TODO: won't work for indexer and ParentRecordCommitOp called directly on the global service or with it passed
# as an argument
# see invenio_rdm_records.requests.user_moderation.tasks.delete_record or CommunitySubmission requests


@pass_to_specialized_service(delegate_to_specialized_service | delegate_to_specialized_service_rdm)
@check_fully_overridden(
    pass_through | pass_through_rdm,
    delegate_to_specialized_service | delegate_to_specialized_service_rdm,
    RDMRecordService,
)
class OARepoRDMService(DelegationToSpecializedServiceMixin, RDMRecordService):
    """RDM service replacement that delegates calls to a specialized services.

    For methods that accept record id, it does so by looking up the persistent identifier
    type and delegating to the service that handles that PID type.

    For create method, it looks at the jsonschema declaration in the data ("$schema" top-level
    property), looks up the service by this schema and calls it.

    Searches have specific handling - a query is run against all the indices and
    then the results are converted to appropripate result classes.
    """

    @property
    def links_item_tpl(self) -> MultiplexingLinks:
        """Item links template."""
        return MultiplexingLinks()

    @unit_of_work()
    @override
    def create(
        self,
        identity: Identity,
        data: dict[str, Any],
        uow: UnitOfWork,
        expand: bool = False,
        schema: str | None = None,
        **kwargs: Any,
    ) -> RecordItem:
        """Create a draft for a new record.

        It does NOT eagerly create the associated record.
        """
        model = self._get_model_from_record_data(data, schema=schema)
        return cast(
            "RecordItem",
            model.service.create(identity=identity, data=data, uow=uow, expand=expand, **kwargs),
        )

    def _get_model_from_record_data(self, data: dict[str, Any], schema: str | None = None) -> Model:
        """Get the model from the record data."""
        if "$schema" in data:
            schema = data["$schema"]
        elif "RDM_PREFERRED_METADATA_SCHEMA" in current_app.config:
            schema = current_app.config["RDM_PREFERRED_METADATA_SCHEMA"]

        if schema is None:
            if len(current_runtime.rdm_models_by_schema) > 1:
                raise UndefinedModelError(
                    "Cannot create a draft without specifying its type. Please add top-level $schema property."
                )
            return next(iter(current_runtime.rdm_models_by_schema.values()))
        if schema in current_runtime.rdm_models_by_schema:
            return current_runtime.rdm_models_by_schema[schema]
        raise UndefinedModelError(f"Model for schema {schema} does not exist.")

    @override
    def _search(
        self,
        action: str,
        identity: Identity,
        params: dict[str, Any],
        search_preference: str | None,
        record_cls: type[RecordItem] | None = None,
        search_opts: Any | None = None,
        extra_filter: Any | None = None,
        permission_action: str = "read",
        versioning: bool = True,
        **kwargs: Any,
    ) -> RecordsSearchV2:
        """Create the search engine DSL."""
        params.update(kwargs)
        # get services that can handle the search request [pid_type -> service]
        services = self._search_eligible_services(
            identity,
            permissions_search_mapping.get(permission_action, permission_action),
            **kwargs,
        )
        if not services:
            raise Forbidden

        queries_list: dict[str, dict] = {}

        for jsonschema, service in services.items():
            search = service._search(  # noqa: SLF001 # calling the same method on delegated
                action=action,
                identity=identity,
                params=copy.deepcopy(params),
                search_preference=search_preference,
                record_cls=record_cls,
                search_opts=search_opts,
                extra_filter=extra_filter,
                permission_action=permission_action,
                versioning=versioning,
                **kwargs,
            )
            queries_list[jsonschema] = search.to_dict()

        params["delegated_query"] = [queries_list, search_opts or self.config.search]

        return super()._search(
            action=action,
            identity=identity,
            params=params,
            search_preference=search_preference,
            record_cls=record_cls,
            search_opts=search_opts,
            extra_filter=extra_filter,
            permission_action=permission_action,
            versioning=versioning,
            **kwargs,
        )

    def _search_eligible_services(
        self, identity: Identity, permission_action: str, **kwargs: Any
    ) -> dict[str, RDMRecordService]:
        """Get a list of eligible RDM record services."""
        return {
            model.record_json_schema: cast("RDMRecordService", model.service)
            for model in current_runtime.rdm_models
            if model.service.check_permission(identity, permission_action, **kwargs)
        }

    @override
    def oai_result_item(self, identity: Identity, oai_record_source: dict[str, Any]) -> RecordItem:
        """Serialize an oai record source to a record item."""
        model = self._get_model_from_record_data(oai_record_source)
        service: RDMRecordService = cast("RDMRecordService", model.service)
        return cast("RecordItem", service.oai_result_item(identity, oai_record_source))

    @override
    def rebuild_index(self, identity: Identity) -> Literal[True]:
        """Rebuild the search index for all records."""
        for model in current_runtime.rdm_models:
            if hasattr(model.service, "rebuild_index"):
                model.service.rebuild_index(identity)
            else:
                raise NotImplementedError(f"Model {model} does not support rebuilding index.")
        return True

    @unit_of_work()
    @override
    def cleanup_drafts(
        self,
        timedelta: datetime.timedelta,
        uow: UnitOfWork | None = None,
        search_gc_deletes: int = 60,
    ) -> None:
        for model in current_runtime.rdm_models:
            cleanup_drafts = getattr(model.service, "cleanup_drafts", None)
            if cleanup_drafts:
                cleanup_drafts(timedelta, uow=uow, search_gc_deletes=search_gc_deletes)
            else:
                raise NotImplementedError(f"Model {model} does not support cleaning up drafts.")

    @unit_of_work()
    @override
    def reindex_latest_first(
        self,
        identity: Identity,
        search_preference: str | None = None,
        extra_filter: Any | None = None,
        uow: UnitOfWork | None = None,
        **kwargs: Any,
    ) -> Literal[True]:
        for model in current_runtime.rdm_models:
            reindex_latest_first = getattr(model.service, "reindex_latest_first", None)
            if reindex_latest_first:
                reindex_latest_first(
                    identity,
                    search_preference=search_preference,
                    extra_filter=extra_filter,
                    uow=uow,
                    **kwargs,
                )
            else:
                raise NotImplementedError(f"Model {model} does not support rebuilding index.")

        return True

    @override
    def reindex(
        self,
        identity: Identity,
        params: dict[str, tuple[str, ...]] | None = None,
        search_preference: str | None = None,
        search_query: Any | None = None,
        extra_filter: Any | None = None,
        **kwargs: Any,
    ) -> Literal[True]:
        for model in current_runtime.rdm_models:
            if hasattr(model.service, "reindex"):
                model.service.reindex(
                    identity,
                    params=params,
                    search_preference=search_preference,
                    search_query=search_query,
                    extra_filter=extra_filter,
                    **kwargs,
                )
            else:
                raise NotImplementedError(f"Model {model} does not support rebuilding index.")
        return True

    @override
    def on_relation_update(
        self,
        identity: Identity,
        record_type: str,
        records_info: list[Any],
        notif_time: str,
        limit: int = 100,
    ) -> Literal[True]:
        for model in current_runtime.rdm_models:
            if hasattr(model.service, "on_relation_update"):
                model.service.on_relation_update(
                    identity,
                    record_type,
                    records_info,
                    notif_time,
                    limit=limit,
                )
            else:
                raise NotImplementedError(f"Model {model} does not support relation updates.")  # or pass or to do?
        return True
