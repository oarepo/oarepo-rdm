from flask_resources import ResponseHandler
from oarepo_global_search.resources.records.response import GlobalSearchResponseHandler
from oarepo_rdm.proxies import current_oarepo_rdm


def make_response_handlers_property(original_response_handlers: dict[str, ResponseHandler]):
    def response_handlers(self)->dict[str, ResponseHandler]:
        entrypoint_response_handlers = {} # ?
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

        ret = {
            **original_response_handlers,
            "application/vnd.inveniordm.v1+json": GlobalSearchResponseHandler(
                serializers
            ),
            **entrypoint_response_handlers,
        }
        return ret
    return response_handlers