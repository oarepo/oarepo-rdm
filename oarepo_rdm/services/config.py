from invenio_rdm_records.services.config import RDMRecordServiceConfig
from oarepo_runtime.services.config.service import PermissionsPresetsConfigMixin
from invenio_records_permissions import RecordPermissionPolicy


from invenio_drafts_resources.services import (
    RecordServiceConfig as InvenioRecordDraftsServiceConfig,
)
from invenio_records_resources.services import (
    ConditionalLink,
    LinksTemplate,
    RecordLink,
    pagination_links,
)
"""
from modelc.records.api import ModelcDraft, ModelcRecord
from modelc.services.records.permissions import ModelcPermissionPolicy
from modelc.services.records.results import ModelcRecordItem, ModelcRecordList
from modelc.services.records.schema import ModelcSchema
from modelc.services.records.search import ModelcDraftSearchOptions, ModelcSearchOptions
"""
from oarepo_runtime.services.components import OwnersComponent, process_service_configs
from oarepo_runtime.services.config import (
    has_draft,
    has_permission,
    has_published_record,
    is_published_record,
)
from oarepo_runtime.services.config.service import PermissionsPresetsConfigMixin
from oarepo_runtime.services.records import pagination_links_html
from invenio_rdm_records.records.api import RDMRecord, RDMDraft
from oarepo_runtime.services.results import RecordItem, RecordList

from invenio_drafts_resources.services import (
    RecordServiceConfig as InvenioRecordDraftsServiceConfig,
)


class ModelcRecordItem(RecordItem):
    """ModelcRecord record item."""

    components = [*RecordItem.components]


class ModelcRecordList(RecordList):
    """ModelcRecord record list."""

    components = [*RecordList.components]


class DummyPermissionPolicy(RecordPermissionPolicy):
    can_search = []
    can_read = []
    can_create = []
    can_update = []
    can_delete = []
    can_manage = []
    can_read_files = []
    can_update_files = []
    



class OARepoRDMServiceConfig(PermissionsPresetsConfigMixin, InvenioRecordDraftsServiceConfig):

    base_permission_policy_cls = DummyPermissionPolicy

    PERMISSIONS_PRESETS = ["everyone"]

    @property
    def components(self):
        return process_service_configs(self, OwnersComponent)



    result_item_cls = ModelcRecordItem
    result_list_cls = ModelcRecordList
    record_cls = RDMRecord
    draft_cls = RDMDraft