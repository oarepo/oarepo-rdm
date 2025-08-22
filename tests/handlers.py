#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Handler classes. Should be converted to exporters."""

# TODO: convert to exporters
from invenio_rdm_records.resources.serializers.dublincore import DublinCoreXMLSerializer
from invenio_records_resources.resources.records.headers import etag_headers
from oarepo_runtime.resources.responses import OAIExportableResponseHandler


class ModelaDublinCoreXMLSerializer(DublinCoreXMLSerializer):
    """Dublin core serializer for model a."""


class ModelbDublinCoreXMLSerializer(DublinCoreXMLSerializer):
    """Dublin core serializer for model b."""


class ModelcDublinCoreXMLSerializer(DublinCoreXMLSerializer):
    """Dublin core serializer for model c."""


modela_handler = {
    "application/x-dc+xml": OAIExportableResponseHandler(
        export_code="dc_xml",
        name="Dublin Core XML",
        serializer=ModelaDublinCoreXMLSerializer(),
        headers=etag_headers,
        oai_metadata_prefix="oai_dc",
        oai_schema="http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
        oai_namespace="http://www.openarchives.org/OAI/2.0/oai_dc/",
    )
}
modelb_handler = {
    "application/x-dc+xml": OAIExportableResponseHandler(
        export_code="dc_xml",
        name="Dublin Core XML",
        serializer=ModelbDublinCoreXMLSerializer(),
        headers=etag_headers,
        oai_metadata_prefix="oai_dc",
        oai_schema="http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
        oai_namespace="http://www.openarchives.org/OAI/2.0/oai_dc/",
    )
}
modelc_handler = {
    "application/x-dc+xml": OAIExportableResponseHandler(
        export_code="dc_xml",
        name="Dublin Core XML",
        serializer=ModelcDublinCoreXMLSerializer(),
        headers=etag_headers,
        oai_metadata_prefix="oai_dc",
        oai_schema="http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
        oai_namespace="http://www.openarchives.org/OAI/2.0/oai_dc/",
    )
}
