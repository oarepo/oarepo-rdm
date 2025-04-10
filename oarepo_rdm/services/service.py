from invenio_rdm_records.services.services import RDMRecordService
from invenio_records_resources.services.uow import unit_of_work
from oarepo_global_search.proxies import (
    current_global_search,
    current_global_search_service,
)

from oarepo_rdm.errors import UndefinedModelError
from oarepo_rdm.proxies import current_oarepo_rdm


def check_fully_overridden(cls):
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
    }
    # what to do with delete? rdm uses delete_record but does not ban it
    # perhaps it's simpler to just list exceptions than explicitly call super(), it does the same thing?

    for m in cls.mro():
        for name, value in m.__dict__.items():
            if callable(value) and not name.startswith("_"):
                assert (
                    name in cls.__dict__ or name in exceptions
                ), f"Method with name {value.__qualname__} is not overridden in OARepoRDMService."
    return cls


@check_fully_overridden
class OARepoRDMService(RDMRecordService):
    """"""

    def _get_specialized_service(self, id_):
        pid_type = current_oarepo_rdm.get_pid_type_from_pid(id_)
        return current_oarepo_rdm.record_service_from_pid_type(pid_type)

    @unit_of_work()
    def create(self, identity, data, schema=None, uow=None, expand=False, **kwargs):
        """Create a draft for a new record.

        It does NOT eagerly create the associated record.
        """
        if "$schema" in data:
            schema = data["$schema"]
        services = (
            current_global_search.global_search_model_services
        )  # eventually there might be non-global search service that should work with this?
        if len(services) > 1 and not schema:
            raise UndefinedModelError(
                "Cannot create a draft without specifying its type."
            )
        if len(services) == 1:
            service = services[0]
        else:
            for service in services:
                if service.record_cls.schema.value == schema:
                    break
            else:
                raise UndefinedModelError(
                    f"Service for record with schema {schema} does not exist."
                )
        return service.create(
            identity=identity, data=data, uow=uow, expand=expand, **kwargs
        )

    def read(self, identity, id_, expand=False, include_deleted=False):
        return self._get_specialized_service(id_).read(
            identity, id_, expand=expand, include_deleted=include_deleted
        )

    @unit_of_work()
    def delete_record(
        self, identity, id_, data, expand=False, uow=None, revision_id=None
    ):
        return self._get_specialized_service(id_).delete_record(
            identity, id_, expand=expand, uow=uow, revision_id=revision_id
        )

    @unit_of_work()
    def delete_draft(self, identity, id_, revision_id=None, uow=None, **kwargs):
        return self._get_specialized_service(id_).delete_draft(
            identity, id_, revision_id=revision_id, uow=uow, **kwargs
        )

    @unit_of_work()
    def lift_embargo(self, identity, _id, uow=None):
        return self._get_specialized_service(_id).lift_embargo(identity, _id, uow=uow)

    @unit_of_work()
    def import_files(self, identity, id_, uow=None, **kwargs):
        return self._get_specialized_service(id_).import_files(
            identity, id_, uow=uow, **kwargs
        )

    @unit_of_work()
    def mark_record_for_purge(self, identity, id_, expand=False, uow=None):
        return self._get_specialized_service(id_).mark_record_for_purge(
            identity, id_, expand=expand, uow=uow
        )

    @unit_of_work()
    def publish(self, identity, id_, uow=None, expand=False):
        return self._get_specialized_service(id_).publish(
            identity, id_, expand=expand, uow=uow
        )

    @unit_of_work()
    def purge_record(self, identity, id_, uow=None):
        return self._get_specialized_service(id_).purge_record(identity, id_, uow=uow)

    def read_draft(self, identity, id_, expand=False):
        return self._get_specialized_service(id_).read_draft(
            identity, id_, expand=expand
        )

    def read_latest(self, identity, id_, expand=False, **kwargs):
        return self._get_specialized_service(id_).read_latest(
            identity, id_, expand=expand, **kwargs
        )

    @unit_of_work()
    def update(
        self, identity, id_, data, revision_id=None, uow=None, expand=False, **kwargs
    ):
        return self._get_specialized_service(id_).update(
            identity,
            id_,
            data,
            revision_id=revision_id,
            uow=uow,
            expand=expand,
            **kwargs,
        )

    @unit_of_work()
    def update_draft(
        self, identity, id_, data, revision_id=None, uow=None, expand=False
    ):
        return self._get_specialized_service(id_).update_draft(
            identity, id_, data, revision_id=revision_id, uow=uow, expand=expand
        )

    @unit_of_work()
    def restore_record(self, identity, id_, expand=False, uow=None):
        return self._get_specialized_service(id_).restore_record(
            identity, id_, expand=expand, uow=uow
        )

    def scan_versions(
        self,
        identity,
        id_,
        params=None,
        search_preference=None,
        expand=False,
        permission_action="read_deleted",
        **kwargs,
    ):
        return self._get_specialized_service(id_).scan_versions(
            identity,
            id_,
            params=params,
            search_preferences=search_preference,
            expand=expand,
            permissions_action=permission_action,
            **kwargs,
        )

    def search_versions(
        self, identity, id_, params=None, search_preference=None, expand=False, **kwargs
    ):
        return self._get_specialized_service(id_).search_versions(
            identity,
            id_,
            params=params,
            search_preferences=search_preference,
            expand=expand,
            **kwargs,
        )

    @unit_of_work()
    def set_quota(
        self,
        identity,
        id_,
        data,
        files_attr="files",
        uow=None,
    ):
        return self._get_specialized_service(id_).set_quota(
            identity, id_, data=data, files_attr=files_attr, uow=uow
        )

    @unit_of_work()
    def set_user_quota(
        self,
        identity,
        id_,
        data,
        uow=None,
    ):
        return self._get_specialized_service(id_).set_user_quota(
            identity, id_, data=data, uow=uow
        )

    @unit_of_work()
    def unmark_record_for_purge(self, identity, id_, expand=False, uow=None):
        return self._get_specialized_service(id_).unmark_record_for_purge(
            identity, id_, expand=expand, uow=uow
        )

    @unit_of_work()
    def update_tombstone(self, identity, id_, data, expand=False, uow=None):
        return self._get_specialized_service(id_).update_tombstone(
            identity, id_, data=data, expand=expand, uow=uow
        )

    def validate_draft(self, identity, id_, ignore_field_permissions=False):
        return self._get_specialized_service(id_).validate_draft(
            identity, id_, ignore_field_permissions=ignore_field_permissions
        )

    @unit_of_work()
    def edit(self, identity, id_, uow=None, expand=False, **kwargs):
        return self._get_specialized_service(id_).edit(
            identity, id_, uow=uow, expand=expand, **kwargs
        )

    @unit_of_work()
    def new_version(self, identity, id_, uow=None, expand=False, **kwargs):
        return self._get_specialized_service(id_).new_version(
            identity, id_, uow=uow, expand=expand, **kwargs
        )

    def search(self, identity, params, *args, extra_filter=None, **kwargs):
        return current_global_search_service.search(
            identity, params, *args, extra_filter=extra_filter, **kwargs
        )

    def search_drafts(self, identity, params, *args, extra_filter=None, **kwargs):
        return current_global_search_service.search_drafts(
            identity, params, *args, extra_filter=extra_filter, **kwargs
        )

    def scan(
        self, identity, params=None, search_preference=None, expand=False, **kwargs
    ):
        return current_global_search_service.scan(
            identity,
            params,
            search_preference=search_preference,
            expand=expand,
            **kwargs,
        )

    def oai_result_item(self, identity, oai_record_source):
        raise NotImplementedError()

    def rebuild_index(self, identity, uow=None):
        raise NotImplementedError()

    @unit_of_work()
    def cleanup_drafts(self, timedelta, uow=None, search_gc_deletes=60):
        raise NotImplementedError()

    @unit_of_work()
    def reindex_latest_first(
        self, identity, search_preference=None, extra_filter=None, uow=None, **kwargs
    ):
        raise NotImplementedError()

    def reindex(
        self,
        identity,
        params=None,
        search_preference=None,
        search_query=None,
        extra_filter=None,
        **kwargs,
    ):
        raise NotImplementedError()

    def on_relation_update(
        self, identity, record_type, records_info, notif_time, limit=100
    ):
        raise NotImplementedError()
