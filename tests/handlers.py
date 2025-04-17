from invenio_rdm_records.resources.serializers.dublincore import DublinCoreXMLSerializer
from invenio_records_resources.resources.records.headers import etag_headers
from oarepo_runtime.resources.responses import OAIExportableResponseHandler

class ModelaDublinCoreXMLSerializer(DublinCoreXMLSerializer):
    """"""

class ModelbDublinCoreXMLSerializer(DublinCoreXMLSerializer):
    """"""

class ModelcDublinCoreXMLSerializer(DublinCoreXMLSerializer):
    """"""

modela_handler = {"application/x-dc+xml": OAIExportableResponseHandler(
                export_code="dc_xml", name="Dublin Core XML", serializer=ModelaDublinCoreXMLSerializer(),
                headers=etag_headers, oai_metadata_prefix="oai_dc",
                oai_schema="http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
                oai_namespace="http://www.openarchives.org/OAI/2.0/oai_dc/"
            )
}
modelb_handler = {"application/x-dc+xml": OAIExportableResponseHandler(
                export_code="dc_xml", name="Dublin Core XML", serializer=ModelbDublinCoreXMLSerializer(),
                headers=etag_headers, oai_metadata_prefix="oai_dc",
                oai_schema="http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
                oai_namespace="http://www.openarchives.org/OAI/2.0/oai_dc/"
            )
}