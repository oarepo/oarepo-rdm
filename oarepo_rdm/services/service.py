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

from typing import TYPE_CHECKING, Any, Literal, cast, override

from invenio_rdm_records.services.services import RDMRecordService
from invenio_records_resources.services.uow import UnitOfWork, unit_of_work
from oarepo_runtime.proxies import current_runtime

from oarepo_rdm.errors import UndefinedModelError

if TYPE_CHECKING:
    import datetime

    from invenio_access.permissions import Identity
    from invenio_records_resources.services.files.results import FileList
    from invenio_records_resources.services.records.results import (
        RecordItem,
        RecordList,
    )
    from oarepo_runtime.api import Model


def check_fully_overridden(cls: type) -> type:
    """Check that all methods are fully overridden in the subclass."""
    exceptions = {
        "create_search",
        "search_request",
        "check_revision_id",
        "read_many",
        "read_all",
        "delete",
        "permission_policy",
        "check_permission",
        "require_permission",
        "run_components",
        "result_item",
        "result_list",
        "record_to_index",
        "scan_expired_embargos",
        "exists",
        "cleanup_record",
        "search_revisions",
        "read_revision",
        "create_or_update_many",
        "result_bulk_item",
        "result_bulk_list",
        # out of place
        "set_user_quota",
    }

    for m in cls.mro()[1:]:
        # go through base classes and check if methods defined on them
        # are either in the list of exceptions, or are overriden in the class
        for name, value in m.__dict__.items():
            if callable(value) and not name.startswith("_") and not (name in cls.__dict__ or name in exceptions):
                raise TypeError(f"Method with name {value.__qualname__} is not overridden in OARepoRDMService.")
    return cls


@check_fully_overridden
class OARepoRDMService(RDMRecordService):
    """RDM service replacement that delegates calls to a specialized services.

    For methods that accept record id, it does so by looking up the persistent identifier
    type and delegating to the service that handles that PID type.

    For create method, it looks at the jsonschema declaration in the data ("$schema" top-level
    property), looks up the service by this schema and calls it.

    Searches have specific handling - a query is run against all the indices and
    then the results are converted to appropripate result classes.
    """

    def _get_specialized_service(self, pid_value: str) -> RDMRecordService:
        """Get a specialized service based on the pid_value of the record."""
        pid_type = current_runtime.find_pid_type_from_pid(pid_value)
        return cast("RDMRecordService", current_runtime.model_by_pid_type[pid_type].service)

    @unit_of_work()
    @override
    def create(  # pyright: reportIncompatibleMethodOverride=False # type: ignore[override]
        self,
        identity: Identity,
        data: dict[str, Any],
        uow: UnitOfWork | None = None,
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
    def read(  # type: ignore[override]
        self,
        identity: Identity,
        id_: str,
        expand: bool = False,
        include_deleted: bool = False,
    ) -> RecordItem:
        """Read a record.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param expand: if True, expand fields such as files and requests.
        :param include_deleted: if True, include deleted records in the response,
                    otherwise RecordDeletedException is raised for deleted records.
        """
        return cast(
            "RecordItem",
            self._get_specialized_service(id_).read(identity, id_, expand=expand, include_deleted=include_deleted),
        )

    @unit_of_work()
    @override
    def delete_record(
        self,
        identity: Identity,
        id_: str,
        data: dict[str, Any],
        expand: bool = False,
        uow: UnitOfWork | None = None,
        revision_id: str | None = None,
    ) -> RecordItem:
        """Soft-delete a record.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param data: the data with a reason why the record is deleted.
        :param expand: if True, expand fields such as files and requests.
        :param uow: the unit of work to use.
        :param revision_id: the revision ID of the record. If provided, check that
                the actual record revision is equal and if not, raise a revision conflict
                exception.
        """
        return cast(
            "RecordItem",
            self._get_specialized_service(id_).delete_record(
                identity,
                id_,
                data=data,
                expand=expand,
                uow=uow,
                revision_id=revision_id,
            ),
        )

    @unit_of_work()
    @override
    def delete_draft(
        self,
        identity: Identity,
        id_: str,
        revision_id: str | None = None,
        uow: UnitOfWork | None = None,
    ) -> Literal[True]:
        """Delete a draft record.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the draft record.
        :param revision_id: the revision ID of the draft record. If provided, check that
                the actual draft revision is equal and if not, raise a revision conflict
        :param uow: the unit of work to use.
        """
        return self._get_specialized_service(id_).delete_draft(  # type: ignore[no-any-return]
            identity, id_, revision_id=revision_id, uow=uow
        )

    @unit_of_work()
    @override
    def lift_embargo(self, identity: Identity, _id: str, uow: UnitOfWork | None = None) -> None:
        """Lift the embargo on a record.

        :param identity: the identity of the user making the request.
        :param _id: the persistent identifier of the record.
        :param uow: the unit of work to use.
        """
        self._get_specialized_service(_id).lift_embargo(identity, _id, uow=uow)

    @unit_of_work()
    @override
    def import_files(self, identity: Identity, id_: str, uow: UnitOfWork | None = None, **kwargs: Any) -> FileList:
        """Import files from a published record to a draft record that was created from the published one.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the draft record.
        :param uow: the unit of work to use.
        """
        return cast(
            "FileList",
            self._get_specialized_service(id_).import_files(identity, id_, uow=uow, **kwargs),
        )

    @unit_of_work()
    @override
    def mark_record_for_purge(
        self,
        identity: Identity,
        id_: str,
        expand: bool = False,
        uow: UnitOfWork | None = None,
    ) -> RecordItem:
        """Mark a soft-deleted record for a purge.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param expand: if True, expand fields such as files and requests.
        :param uow: the unit of work to use.
        """
        return cast(
            "RecordItem",
            self._get_specialized_service(id_).mark_record_for_purge(identity, id_, expand=expand, uow=uow),
        )

    @unit_of_work()
    @override
    def publish(
        self,
        identity: Identity,
        id_: str,
        uow: UnitOfWork | None = None,
        expand: bool = False,
    ) -> RecordItem:
        """Publish a draft record.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the draft record.
        :param uow: the unit of work to use.
        :param expand: whether to expand the response.
        """
        return cast(
            "RecordItem",
            self._get_specialized_service(id_).publish(identity, id_, expand=expand, uow=uow),
        )

    @unit_of_work()
    @override
    def purge_record(  # pyright: reportIncompatibleMethodOverride=False # type: ignore[override]
        self, identity: Identity, id_: str, uow: UnitOfWork | None = None
    ) -> None:
        """Purge a soft-deleted record.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param uow: the unit of work to use.
        """
        self._get_specialized_service(id_).purge_record(identity, id_, uow=uow)

    @override
    def read_draft(self, identity: Identity, id_: str, expand: bool = False) -> RecordItem:
        """Read a draft record.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the draft record.
        :param expand: if True, expand fields such as files and requests.
        """
        return cast(
            "RecordItem",
            self._get_specialized_service(id_).read_draft(identity, id_, expand=expand),
        )

    @override
    def read_latest(self, identity: Identity, id_: str, expand: bool = False) -> RecordItem:
        """Read the latest version of a record.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param expand: if True, expand fields such as files and requests.
        """
        return cast(
            "RecordItem",
            self._get_specialized_service(id_).read_latest(identity, id_, expand=expand),
        )

    @unit_of_work()
    @override
    def update(
        self,
        identity: Identity,
        id_: str,
        data: dict,
        revision_id: str | None = None,
        uow: UnitOfWork | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordItem:
        """Update a record.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param data: the data to update the record with.
        :param revision_id: optimistic concurrency control revision ID.
        :param uow: the unit of work to use.
        :param expand: whether to expand the response.
        :param kwargs: additional keyword arguments.
        """
        return cast(
            "RecordItem",
            self._get_specialized_service(id_).update(
                identity,
                id_,
                data,
                revision_id=revision_id,
                uow=uow,
                expand=expand,
                **kwargs,
            ),
        )

    @unit_of_work()
    @override
    def update_draft(
        self,
        identity: Identity,
        id_: str,
        data: dict,
        revision_id: str | None = None,
        uow: UnitOfWork | None = None,
        expand: bool = False,
    ) -> RecordItem:
        """Update a draft record.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the draft record.
        :param data: the data to update the draft record with.
        :param revision_id: optimistic concurrency control revision ID.
        :param uow: the unit of work to use.
        :param expand: whether to expand the response.
        """
        return cast(
            "RecordItem",
            self._get_specialized_service(id_).update_draft(
                identity, id_, data, revision_id=revision_id, uow=uow, expand=expand
            ),
        )

    @unit_of_work()
    @override
    def restore_record(
        self,
        identity: Identity,
        id_: str,
        expand: bool = False,
        uow: UnitOfWork | None = None,
    ) -> None:
        """Restore a soft-deleted record.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param expand: if True, expand fields such as files and requests.
        :param uow: the unit of work to use.
        """
        self._get_specialized_service(id_).restore_record(identity, id_, expand=expand, uow=uow)

    @override
    def scan_versions(
        self,
        identity: Identity,
        id_: str,
        params: dict[str, list[str]] | None = None,
        search_preference: str | None = None,
        expand: bool = False,
        permission_action: str = "read_deleted",
        **kwargs: Any,
    ) -> RecordList:
        """Return all versions of a record, optionally with a filter applied.

        This call uses opensearch `scan` API to retrieve all versions of a record.
        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param params: additional query parameters.
        :param search_preference: the search preference to use.
        :param expand: if True, expand fields such as files and requests.
        :param permission_action: the permission action to use.
        :param kwargs: additional keyword arguments.
        """
        return cast(
            "RecordList",
            self._get_specialized_service(id_).scan_versions(
                identity,
                id_,
                params=params,
                search_preferences=search_preference,
                expand=expand,
                permissions_action=permission_action,
                **kwargs,
            ),
        )

    @override
    def search_versions(  # type: ignore[override] # pyright: reportIncompatibleMethodOverride=False
        self,
        identity: Identity,
        id_: str,
        params: dict[str, list[str]] | None = None,
        search_preference: str | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordList:
        """Search for all versions of a record, optionally with a filter applied.

        This call uses opensearch `search` API to retrieve all versions of a record.
        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param params: additional query parameters.
        :param search_preference: the search preference to use.
        :param expand: if True, expand fields such as files and requests.
        :param kwargs: additional keyword arguments.
        """
        return cast(
            "RecordList",
            self._get_specialized_service(id_).search_versions(
                identity,
                id_,
                params=params,
                search_preferences=search_preference,
                expand=expand,
                **kwargs,
            ),
        )

    @unit_of_work()
    @override
    def set_quota(
        self,
        identity: Identity,
        id_: str,
        data: dict[str, Any],
        files_attr: str = "files",
        uow: UnitOfWork | None = None,
    ) -> Literal[True]:
        """Set the quota for a record.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param data: the quota data to set.
        :param files_attr: the files attribute to use.
        :param uow: the unit of work to use.
        """
        return self._get_specialized_service(id_).set_quota(  # type: ignore[no-any-return]
            identity, id_, data=data, files_attr=files_attr, uow=uow
        )

    @unit_of_work()
    @override
    def unmark_record_for_purge(
        self,
        identity: Identity,
        id_: str,
        expand: bool = False,
        uow: UnitOfWork | None = None,
    ) -> RecordItem:
        """Unmark a record for purge.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param expand: if True, expand fields such as files and requests.
        :param uow: the unit of work to use.
        """
        return cast(
            "RecordItem",
            self._get_specialized_service(id_).unmark_record_for_purge(identity, id_, expand=expand, uow=uow),
        )

    @unit_of_work()
    @override
    def update_tombstone(
        self,
        identity: Identity,
        id_: str,
        data: dict[str, Any],
        expand: bool = False,
        uow: UnitOfWork | None = None,
    ) -> RecordItem:
        """Update the tombstone of a deleted record.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param data: the tombstone data to update.
        :param expand: if True, expand fields such as files and requests.
        :param uow: the unit of work to use.
        """
        return cast(
            "RecordItem",
            self._get_specialized_service(id_).update_tombstone(identity, id_, data=data, expand=expand, uow=uow),
        )

    @override
    def validate_draft(self, identity: Identity, id_: str, ignore_field_permissions: bool = False) -> None:
        self._get_specialized_service(id_).validate_draft(
            identity, id_, ignore_field_permissions=ignore_field_permissions
        )

    @unit_of_work()
    @override
    def edit(
        self,
        identity: Identity,
        id_: str,
        uow: UnitOfWork | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordItem:
        """Edit a record.

        This method creates a draft record from a published record and return it.
        When the draft is published, the original record is updated with the new data.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param uow: the unit of work to use.
        :param expand: if True, expand fields such as files and requests.
        :param kwargs: additional keyword arguments.

        :return: the edited draft record.
        """
        return cast(
            "RecordItem",
            self._get_specialized_service(id_).edit(identity, id_, uow=uow, expand=expand, **kwargs),
        )

    @unit_of_work()
    @override
    def new_version(
        self,
        identity: Identity,
        id_: str,
        uow: UnitOfWork | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordItem:
        """Create a new version of a record.

        This method creates a draft by copying the existing record data
        and allowing for modifications. The draft will have a new persistent identifier.
        When the draft is published, a new published record with the same PID is created.

        :param identity: the identity of the user making the request.
        :param id_: the persistent identifier of the record.
        :param uow: the unit of work to use.
        :param expand: if True, expand fields such as files and requests.
        :param kwargs: additional keyword arguments.

        :return: the new version of the record.
        """
        return cast(
            "RecordItem",
            self._get_specialized_service(id_).new_version(identity, id_, uow=uow, expand=expand, **kwargs),
        )

    @override
    def search(
        self,
        identity: Identity,
        params: dict[str, tuple[str, ...]] | None = None,
        search_preference: str | None = None,
        expand: bool = False,
        extra_filter: Any | None = None,
        **kwargs: Any,
    ) -> RecordList:
        """Search for records.

        :param identity: the identity of the user making the request.
        :param params: the search parameters.
        :param search_preference: the search preference.
        :param expand: whether to expand the results.
        :param extra_filter: any extra filter to apply.
        :param kwargs: any additional keyword arguments.
        """
        raise NotImplementedError

    @override
    def search_drafts(
        self,
        identity: Identity,
        params: dict[str, tuple[str, ...]] | None = None,
        search_preference: str | None = None,
        expand: bool = False,
        extra_filter: Any | None = None,
        **kwargs: Any,
    ) -> RecordList:
        """Search for user records.

        Note: both drafts and published records where the identity is an owner are returned.

        :param identity: the identity of the user making the request.
        :param params: the search parameters.
        :param search_preference: the search preference.
        :param expand: whether to expand the results.
        :param extra_filter: any extra filter to apply.
        :param kwargs: any additional keyword arguments.
        """
        raise NotImplementedError

    @override
    def scan(
        self,
        identity: Identity,
        params: dict[str, tuple[str, ...]] | None = None,
        search_preference: str | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordList:
        """Scan for records.

        :param identity: the identity of the user making the request.
        :param params: the search parameters.
        :param search_preference: the search preference.
        :param expand: whether to expand the results.
        :param kwargs: any additional keyword arguments.
        """
        raise NotImplementedError

    @override
    def oai_result_item(self, identity: Identity, oai_record_source: dict[str, Any]) -> RecordItem:
        """Serialize an oai record source to a record item."""
        model = self._get_model_from_record_data(oai_record_source)
        service: RDMRecordService = cast("RDMRecordService", model.service)
        return cast("RecordItem", service.oai_result_item(identity, oai_record_source))

    @override
    def rebuild_index(self, identity: Identity, uow: UnitOfWork | None = None) -> None:
        """Rebuild the search index for all records."""
        for model in current_runtime.rdm_models:
            if hasattr(model.service, "rebuild_index"):
                model.service.rebuild_index(identity, uow=uow)
            else:
                raise NotImplementedError(f"Model {model} does not support rebuilding index.")

    @unit_of_work()
    @override
    def cleanup_drafts(
        self,
        timedelta: datetime.timedelta,
        uow: UnitOfWork | None = None,
        search_gc_deletes: int = 60,
    ) -> None:
        for model in current_runtime.rdm_models:
            if hasattr(model.service, "cleanup_drafts"):
                model.service.cleanup_drafts(timedelta, uow=uow, search_gc_deletes=search_gc_deletes)
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
    ) -> None:
        for model in current_runtime.rdm_models:
            if hasattr(model.service, "reindex_latest_first"):
                model.service.reindex_latest_first(
                    identity,
                    search_preference=search_preference,
                    extra_filter=extra_filter,
                    uow=uow,
                    **kwargs,
                )
            else:
                raise NotImplementedError(f"Model {model} does not support rebuilding index.")

    @override
    def reindex(
        self,
        identity: Identity,
        params: dict[str, tuple[str, ...]] | None = None,
        search_preference: str | None = None,
        search_query: str | None = None,
        extra_filter: Any | None = None,
        **kwargs: Any,
    ) -> None:
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

    @override
    def on_relation_update(
        self,
        identity: Identity,
        record_type: str,
        records_info: Any,
        notif_time: datetime.datetime,
        limit: int = 100,
    ) -> None:
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
                raise NotImplementedError(f"Model {model} does not support relation updates.")
