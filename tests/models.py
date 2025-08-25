#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.facets import TermsFacet
from oarepo_model.api import model
from oarepo_model.customizations import AddMetadataExport
from oarepo_model.presets.drafts import drafts_presets
from oarepo_model.presets.rdm import rdm_presets
from oarepo_model.presets.records_resources import records_resources_presets
from oarepo_runtime.api import Export

from oarepo_rdm.oai import oai_presets

from .exports import (
    ModelaDublinCoreXMLSerializer,
    ModelbDublinCoreXMLSerializer,
    ModelcDublinCoreXMLSerializer,
)

modela = model(
    "modela",
    version="1.0.0",
    presets=[records_resources_presets, drafts_presets, rdm_presets, oai_presets],
    types=[
        {
            "Metadata": {
                "properties": {
                    "title": {"type": "keyword"},
                    "adescription": {"type": "keyword"},
                },
            },
        }
    ],
    metadata_type="Metadata",
    customizations=[
        AddMetadataExport(
            Export(
                code="dc_xml",
                name=_("Dublin Core XML"),
                mimetype="application/x-dc+xml",
                serializer=ModelaDublinCoreXMLSerializer(),
                oai_metadata_prefix="oai_dc",
                oai_schema="http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
                oai_namespace="http://www.openarchives.org/OAI/2.0/oai_dc/",
            )
        )
    ],
)

modelb = model(
    "modelb",
    version="1.0.0",
    presets=[records_resources_presets, drafts_presets, rdm_presets, oai_presets],
    types=[
        {
            "Metadata": {
                "properties": {
                    "title": {"type": "keyword"},
                    "bdescription": {"type": "keyword"},
                },
            },
        }
    ],
    metadata_type="Metadata",
    customizations=[
        AddMetadataExport(
            Export(
                code="dc_xml",
                name=_("Dublin Core XML"),
                mimetype="application/x-dc+xml",
                serializer=ModelbDublinCoreXMLSerializer(),
                oai_metadata_prefix="oai_dc",
                oai_schema="http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
                oai_namespace="http://www.openarchives.org/OAI/2.0/oai_dc/",
            )
        )
    ],
)

modelc = model(
    "modelc",
    version="1.0.0",
    presets=[records_resources_presets, drafts_presets, rdm_presets, oai_presets],
    types=[
        {
            "Metadata": {
                "properties": {
                    "title": {"type": "keyword"},
                    "cdescription": {"type": "keyword"},
                },
            },
        }
    ],
    metadata_type="Metadata",
    customizations=[
        AddMetadataExport(
            Export(
                code="dc_xml",
                name=_("Dublin Core XML"),
                mimetype="application/x-dc+xml",
                serializer=ModelcDublinCoreXMLSerializer(),
                oai_metadata_prefix="oai_dc",
                oai_schema="http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
                oai_namespace="http://www.openarchives.org/OAI/2.0/oai_dc/",
            )
        )
    ],
)

assert "metadata_adescription" not in modela.RecordServiceConfig.search.facets, (
    "Remove this assert when facets are supported in oarepo-model"
)

modela.RecordServiceConfig.search.facets["metadata_adescription"] = TermsFacet(
    field="metadata.adescription", label="A Description"
)
