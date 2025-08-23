from invenio_rdm_records.services.results import RDMRecordList
from oarepo_runtime import current_runtime


class MultiplexingResultList(RDMRecordList):
    """Multiplexing result list for the RDM service."""

    @property
    def hits(self):
        """Iterator over the hits."""

        for hit in self._results:
            # Load dump
            record_dict = hit.to_dict()

            schema = hit["$schema"]
            publication_status = hit.get("publication_status", "published")

            delegated_model = current_runtime.rdm_models_by_schema[schema]
            delegated_service = delegated_model.service

            if publication_status == "draft":
                record = delegated_service.draft_cls.loads(record_dict)
            else:
                record = delegated_service.record_cls.loads(record_dict)

            # Project the record
            projection = delegated_service.schema.dump(
                record,
                context=dict(
                    identity=self._identity,
                    record=record,
                    meta=hit.meta,
                ),
            )
            if self._links_item_tpl:
                projection["links"] = delegated_service.links_item_tpl.expand(
                    self._identity, record
                )

            yield projection
