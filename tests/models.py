#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from flask import Blueprint
from invenio_i18n import lazy_gettext as _
from invenio_records_permissions.generators import AnyUser, SystemProcess
from invenio_records_resources.services.records.facets import TermsFacet
from oarepo_model.api import model
from oarepo_model.customizations import (
    AddDefaultSearchFields,
    AddMetadataExport,
    SetPermissionPolicy,
)
from oarepo_runtime.services.config import EveryonePermissionPolicy

from oarepo_rdm.model.presets import (
    rdm_basic_preset,
    rdm_complete_preset,
    rdm_minimal_preset,
)

from .exports import (
    ModelaDublinCoreXMLSerializer,
    ModelaTestSerializer,
    ModelbDublinCoreXMLSerializer,
    ModelbTestSerializer,
    ModelcDublinCoreXMLSerializer,
)


class PermissionPolicyWithModelAPermission(EveryonePermissionPolicy):
    """Permission policy that adds model_a_specific_action for testing."""

    can_model_a_specific_action = (SystemProcess(), AnyUser())


modela = model(
    "modela",
    version="1.0.0",
    presets=[
        rdm_minimal_preset,
    ],
    configuration={"ui_blueprint_name": "modela_ui"},
    types=[
        {
            "Metadata": {
                "properties": {
                    "title": {"type": "fulltext+keyword"},
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
        AddMetadataExport(
            code="test",
            name=_("Test export"),
            mimetype="application/test+json",
            serializer=ModelaTestSerializer(),
        ),
        SetPermissionPolicy(PermissionPolicyWithModelAPermission),
        AddDefaultSearchFields("metadata.title", "metadata.adescription"),
    ],
)
modela.register()

modelb = model(
    "modelb",
    version="1.0.0",
    presets=[
        rdm_basic_preset,
    ],
    types=[
        {
            "Metadata": {
                "properties": {
                    # "title": {"type": "fulltext+keyword"}, - comes from rdb_basic
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
        ),
        AddMetadataExport(
            code="test",
            name=_("Test export"),
            mimetype="application/test+json",
            serializer=ModelbTestSerializer(),
        ),
        AddDefaultSearchFields("metadata.title", "metadata.bdescription"),
    ],
)
modelb.register()

modelc = model(
    "modelc",
    version="1.0.0",
    presets=[
        rdm_complete_preset,
    ],
    types=[
        {
            "Metadata": {
                "properties": {
                    # "title": {"type": "fulltext+keyword"}, - comes from rdm_complete
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
        ),
        AddDefaultSearchFields("metadata.title", "metadata.cdescription"),
    ],
)
modelc.register()

assert "metadata_adescription" not in modela.RecordServiceConfig.search.facets, (
    "Remove this assert when facets are supported in oarepo-model"
)

modela.RecordServiceConfig.search.facets["metadata_adescription"] = TermsFacet(
    field="metadata.adescription", label="A Description"
)


def create_modela_ui_blueprint(app):
    bp = Blueprint("modela_ui", __name__)

    # mock UI resource
    @bp.route("/modela_ui/preview/<pid_value>", methods=["GET"])
    def preview(pid_value: str) -> str:
        return "preview ok"

    @bp.route("/modela_ui/record_detail/<pid_value>", methods=["GET"])
    def record_detail(pid_value: str) -> str:
        return "preview ok"

    @bp.route("/modela_ui/record_latest/<pid_value>", methods=["GET"])
    def record_latest(pid_value: str) -> str:
        return "latest ok"

    @bp.route("/modela_ui/search", methods=["GET"])
    def search() -> str:
        return "search ok"

    @bp.route("/modela_ui/deposit_edit/<pid_value>", methods=["GET"])
    def deposit_edit(pid_value: str) -> str:
        return "deposit_edit ok"

    return bp
