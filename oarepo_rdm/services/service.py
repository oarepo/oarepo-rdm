from invenio_rdm_records.services.services import RDMRecordService
from invenio_records_resources.services.uow import unit_of_work
from oarepo_global_search.proxies import current_global_search_service
from oarepo_rdm.proxies import current_oarepo_rdm

class OARepoRDMService(RDMRecordService):
    """"""
    def _get_specialized_service(self, id_, is_draft=False):
        pid_type = current_oarepo_rdm.get_pid_type_from_pid(id_)
        return current_oarepo_rdm.record_service_from_pid_type(pid_type)

    def read(self, identity, id_, expand=False, include_deleted=False):
        return self._get_specialized_service(id_).read(identity, id_, expand=expand, include_deleted=include_deleted)

    @unit_of_work()
    def delete_record(
        self, identity, id_, data, expand=False, uow=None, revision_id=None
    ):
        return self._get_specialized_service(id_).delete_record(identity, id_, expand=expand, uow=uow, revision_id=revision_id)

    @unit_of_work()
    def lift_embargo(self, identity, id_, uow=None):
        return self._get_specialized_service(id_).lift_embargo(identity, id_, uow=uow)

    @unit_of_work()
    def mark_record_for_purge(self, identity, id_, expand=False, uow=None):
        return self._get_specialized_service(id_).mark_record_for_purge(identity, id_, expand=expand, uow=uow)

    @unit_of_work()
    def publish(self, identity, id_, uow=None, expand=False):
        return self._get_specialized_service(id_).publish(identity, id_, expand=expand, uow=uow)

    @unit_of_work()
    def purge_record(self, identity, id_, uow=None):
        return self._get_specialized_service(id_).purge_record(identity, id_, uow=uow)

    def read_draft(self, identity, id_, expand=False):
        return self._get_specialized_service(id_).read_draft(identity, id_, expand=expand)

    @unit_of_work()
    def update_draft(
        self, identity, id_, data, revision_id=None, uow=None, expand=False
    ):
        return self._get_specialized_service(id_).update_draft(identity,  id_, data, revision_id=revision_id, uow=uow, expand=expand)

    @unit_of_work()
    def restore_record(self, identity, id_, expand=False, uow=None):
        return self._get_specialized_service(id_).restore_record(identity,  id_, expand=expand, uow=uow)

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
        return self._get_specialized_service(id_).scan_versions(identity,  id_, params=params, search_preferences=search_preference,
                                                       expand=expand, permissions_action=permission_action, **kwargs)

    def search_versions(
        self, identity, id_, params=None, search_preference=None, expand=False, **kwargs
    ):
        return self._get_specialized_service(id_).search_versions(identity,  id_, params=params, search_preferences=search_preference,
                                                       expand=expand, **kwargs)

    @unit_of_work()
    def set_quota(
        self,
        identity,
        id_,
        data,
        files_attr="files",
        uow=None,
    ):
        return self._get_specialized_service(id_).set_quota(identity,  id_, data=data, files_attr=files_attr, uow=uow)

    @unit_of_work()
    def set_user_quota(
        self,
        identity,
        id_,
        data,
        uow=None,
    ):
        return self._get_specialized_service(id_).set_user_quota(identity,  id_, data=data, uow=uow)

    @unit_of_work()
    def unmark_record_for_purge(self, identity, id_, expand=False, uow=None):
        return self._get_specialized_service(id_).unmark_record_for_purge(identity,  id_, expand=expand, uow=uow)

    @unit_of_work()
    def update_tombstone(self, identity, id_, data, expand=False, uow=None):
        return self._get_specialized_service(id_).update_tombstone(identity,  id_, data=data, expand=expand, uow=uow)


    def search(self, identity, params, *args, extra_filter=None, ** kwargs):
        return current_global_search_service.search(identity, params, *args, extra_filter=extra_filter, **kwargs)

    def search_drafts(self, identity, params, *args, extra_filter=None, ** kwargs):
        return current_global_search_service.search_drafts(identity, params, *args, extra_filter=extra_filter, **kwargs)



