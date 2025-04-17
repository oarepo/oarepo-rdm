from functools import cached_property
from oarepo_rdm.oai import oai_serializer
from oarepo_rdm.proxies import current_oarepo_rdm
from oarepo_runtime.resources.responses import OAIExportableResponseHandler

class OAIServerMetadataFormats(object):

    def __contains__(self, key):
        return key in self._metadata_formats

    def __getitem__(self, key):
        return self._metadata_formats[key]

    def items(self):
        return self._metadata_formats.items()

    def keys(self):
        return self._metadata_formats.keys()

    def values(self):
        return self._metadata_formats.values()

    @cached_property
    def _metadata_formats(self)->dict:
        """
        Correct handler can't be known here, the configuration in invenio-oaiserver has no access to record schema.
        I'm relying on namespace and schema being same for all metadata formats.
        The oai serializer function universally gets the correct serializer.
        """
        ret = {}
        models = current_oarepo_rdm.rdm_models
        for model in models:
            for handler in model.api_resource_config.response_handlers.values():
                if isinstance(handler, OAIExportableResponseHandler):
                    ret[handler.oai_metadata_prefix] = \
                                            {"namespace": handler.oai_namespace, "schema": handler.oai_schema,
                                             "serializer": (oai_serializer, {"metadata_prefix": handler.oai_metadata_prefix})}

        return ret