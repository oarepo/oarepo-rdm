from functools import cached_property

from oarepo_rdm.proxies import current_oarepo_rdm
from oarepo_runtime.resources.responses import OAIExportableResponseHandler

class OAIServerMetadataFormats(dict):

    def __contains__(self, key):
        return key in self._metadata_formats

    def __getitem__(self, key):
        return self._metadata_formats[key]

    @cached_property
    def _metadata_formats(self)->dict:
        ret = {}
        models = current_oarepo_rdm.rdm_models
        for model in models:
            for handler in model.api_resource_config.response_handlers.values():
                if isinstance(handler, OAIExportableResponseHandler):
                    ret[handler.oai_code] = {"namespace": handler.oai_namespace, "schema": handler.oai_schema,
                                             "serializer": handler.oai_serializer}
        return ret