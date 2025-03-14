from invenio_rdm_records.records import RDMRecord
from invenio_records_resources.references.entity_resolvers.base import EntityResolver, EntityProxy
from oarepo_global_search.proxies import current_global_search
from oarepo_runtime.records.entity_resolvers import RecordProxy

from invenio_records_resources.references.entity_resolvers.records import RecordResolver

class OARepoRecordResolver(RecordResolver):
    """Resolver for records."""
    type_id = "records"

    def __init__(
        self, record_cls=RDMRecord, service_id="records", type_key="record", proxy_cls=RecordProxy
    ):
        """Constructor.

        :param record_cls: The record class to use.
        :param service_id: The record service id.
        :param type_key: The value to use for the TYPE part of the ref_dicts.
        """

        super().__init__(record_cls, service_id, type_key, proxy_cls)

    def matches_entity(self, entity):
        """Check if the entity is a record."""
        for service in current_global_search.global_search_model_services:
            record_cls = service.config.record_cls
            if isinstance(entity, record_cls):
                return True
            if hasattr(service.config, "draft_cls") and isinstance(entity, service.config.draft_cls):
                return True
        return False