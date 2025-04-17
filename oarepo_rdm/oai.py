from oarepo_runtime.resources.responses import OAIExportableResponseHandler
from lxml import etree
from invenio_rdm_records.proxies import current_rdm_records
from collections import defaultdict
from invenio_access.permissions import system_identity
from oarepo_global_search.proxies import current_global_search
from invenio_oaiserver.percolator import percolate_query, _create_percolator_mapping, _build_percolator_index_name
from invenio_records_resources.services.records.results import RecordItem
from invenio_oaiserver.proxies import current_oaiserver
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from oarepo_rdm.proxies import current_oarepo_rdm
from invenio_rdm_records.records.api import RDMRecord


def get_handler_from_metadata_prefix_and_record_schema(metadata_prefix, record_schema):
    for model in current_oarepo_rdm.rdm_models:
        if model.api_service_config.record_cls.schema.value == record_schema:
            for handler in model.api_resource_config.response_handlers.values():
                if isinstance(handler, OAIExportableResponseHandler) and handler.oai_metadata_prefix == metadata_prefix:
                    return handler
    return None

def oai_serializer(pid, record, **serializer_kwargs):
    record_item = record["_source"]
    if not isinstance(record_item, RecordItem):
        record_item = current_rdm_records.records_service.read(system_identity, record_item['id'])
    serializer = get_handler_from_metadata_prefix_and_record_schema(serializer_kwargs["metadata_prefix"],
                                                                    record_item._record.schema).serializer
    return etree.fromstring(
        serializer.serialize_object(record_item.to_dict()).encode(encoding="utf-8")
    )

def get_record(record_uuid, with_deleted=False):
    pids = PersistentIdentifier.query.filter_by(object_uuid=record_uuid).all()
    if not pids:
        raise PIDDoesNotExistError("", record_uuid)
    if len(pids) > 2:
        raise ValueError("Multiple PIDs found")
    for pid in pids:
        if pid.pid_type != "oai":
            target_pid = pid
            break
    actual_record_cls = current_oarepo_rdm.record_cls_from_pid_type(target_pid.pid_type, is_draft=False)
    return actual_record_cls.get_record(record_uuid)

def getrecord_fetcher(record_uuid):
    """Fetch record data as dict with identity check for serialization."""
    record = get_record(record_uuid)
    record_dict = record.dumps()
    record_dict["updated"] = record.updated
    return record_dict

    """
    recid = PersistentIdentifier.get_by_object(
        pid_type="recid", object_uuid=record_id, object_type="rec"
    )

    try:
        return current_rdm_records.records_service.read(g.identity, recid.pid_value)
    except PermissionDeniedError:
        # if it is a restricted record.
        raise PIDDoesNotExistError("recid", None)
    """

def get_service_by_record_schema(record_dict):
    for service in current_global_search.global_search_model_services:
        if not hasattr(service, "record_cls") or not hasattr(service.record_cls, "schema"):
            continue
        if service.record_cls.schema.value == record_dict["$schema"]:
            return service
    return None



def sets_search_all(records):
    # in invenio it's used only for find_sets_for_record, which doesn't use more than one record
    if not records:
        return []

    processed_schemas = set()
    indices_mapping = {}
    records_mapping = defaultdict(list)
    results_for_index = {}
    records_sets_mapping = {}

    for record in records:
        if isinstance(record, RecordItem):
            dumper = record._record.dumper
            record_new = dumper.dump(record._record, record.data) # todo this did not work in the percolator index
            record = record._record.dumps()

        schema = record["$schema"]
        if schema not in processed_schemas:
            service = get_service_by_record_schema(record)
            record_item = service.read(system_identity, record["id"])
            record_index = record_item._record.index._name
            _create_percolator_mapping(record_index)
            percolator_index = _build_percolator_index_name(record_index)
            indices_mapping[schema] = percolator_index
            processed_schemas.add(service)

        records_mapping[schema].append(record)

    for schema, index in indices_mapping.items():
        records = records_mapping[schema]
        record_sets = [[] for _ in range(len(records))]
        result = percolate_query(indices_mapping[schema], documents=records)
        results_for_index[schema] = result
        records_sets_mapping[schema] = record_sets

    prefix = "oaiset-"
    prefix_len = len(prefix)

    for schema, result in results_for_index.items():
        for s in result:
            set_index_id = s["_id"]
            if set_index_id.startswith(prefix):
                set_spec = set_index_id[prefix_len:]
                for record_index in s.get("fields", {}).get(
                    "_percolator_document_slot", []
                ):
                    records_sets_mapping[schema][record_index].append(set_spec)
    return [item for sublist in records_sets_mapping.values() for item in sublist]

def find_sets_for_record(record):
    """Fetch a record's sets."""
    return sets_search_all([record])[0]
