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
from invenio_records_permissions.generators import AnyUser, SystemProcess
from invenio_records_resources.services.records.facets import TermsFacet
from oarepo_model.api import model
from oarepo_model.customizations import AddMetadataExport, SetPermissionPolicy
from oarepo_model.presets.drafts import drafts_preset
from oarepo_model.presets.records_resources import records_resources_preset
from oarepo_runtime.services.config import EveryonePermissionPolicy

from oarepo_rdm.model.presets.rdm import rdm_preset
from oarepo_rdm.oai import oai_preset

from .exports import (
    ModelaDublinCoreXMLSerializer,
    ModelbDublinCoreXMLSerializer,
    ModelcDublinCoreXMLSerializer,
)


class PermissionPolicyWithModelAPermission(EveryonePermissionPolicy):
    """Permission policy that adds model_a_specific_action for testing."""

    can_model_a_specific_action = (SystemProcess(), AnyUser())


modela = model(
    "modela",
    version="1.0.0",
    presets=[records_resources_preset, drafts_preset, rdm_preset, oai_preset],
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
            code="dc_xml",
            name=_("Dublin Core XML"),
            mimetype="application/x-dc+xml",
            serializer=ModelaDublinCoreXMLSerializer(),
            oai_metadata_prefix="oai_dc",
            oai_schema="http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
            oai_namespace="http://www.openarchives.org/OAI/2.0/oai_dc/",
        ),
        SetPermissionPolicy(PermissionPolicyWithModelAPermission),
    ],
)

modelb = model(
    "modelb",
    version="1.0.0",
    presets=[records_resources_preset, drafts_preset, rdm_preset, oai_preset],
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
            code="dc_xml",
            name=_("Dublin Core XML"),
            mimetype="application/x-dc+xml",
            serializer=ModelbDublinCoreXMLSerializer(),
            oai_metadata_prefix="oai_dc",
            oai_schema="http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
            oai_namespace="http://www.openarchives.org/OAI/2.0/oai_dc/",
        )
    ],
)

modelc = model(
    "modelc",
    version="1.0.0",
    presets=[records_resources_preset, drafts_preset, rdm_preset, oai_preset],
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
            code="dc_xml",
            name=_("Dublin Core XML"),
            mimetype="application/x-dc+xml",
            serializer=ModelcDublinCoreXMLSerializer(),
            oai_metadata_prefix="oai_dc",
            oai_schema="http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
            oai_namespace="http://www.openarchives.org/OAI/2.0/oai_dc/",
        )
    ],
)

assert "metadata_adescription" not in modela.RecordServiceConfig.search.facets, (
    "Remove this assert when facets are supported in oarepo-model"
)

modela.RecordServiceConfig.search.facets["metadata_adescription"] = TermsFacet(
    field="metadata.adescription", label="A Description"
)
