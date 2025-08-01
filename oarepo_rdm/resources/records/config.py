from flask_resources import ResponseHandler
from oarepo_global_search.resources.records.response import GlobalSearchResponseHandler
from oarepo_rdm.proxies import current_oarepo_rdm

def global_search_response_handlers():
    serializers = []

    for model in current_oarepo_rdm.rdm_models:
        serializers.append(
            {
                "schema": model.api_service.record_cls.schema.value,
                "serializer": model.api_resource.config.response_handlers[
                    "application/vnd.inveniordm.v1+json"
                ].serializer,
            }
        )

    return GlobalSearchResponseHandler(
                serializers
            )

