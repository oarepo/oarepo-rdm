from invenio_rdm_records.requests.entity_resolvers import EmailResolver
from oarepo_rdm.records.resolver import OARepoRecordResolver

REQUESTS_REGISTERED_RESOLVERS = [EmailResolver(), OARepoRecordResolver()]
