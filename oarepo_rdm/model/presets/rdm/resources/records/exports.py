#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for adding default exports to RDM-complete models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.resources.config import csl_url_args_retriever
from invenio_rdm_records.resources.serializers import (  # type: ignore[reportAttributeAccessIssue]
    BibtexSerializer,  # type: ignore[reportAttributeAccessIssue]
    CSLJSONSerializer,  # type: ignore[reportAttributeAccessIssue]
    CSVRecordSerializer,  # type: ignore[reportAttributeAccessIssue]
    DataCite43XMLSerializer,  # type: ignore[reportAttributeAccessIssue]
    DataPackageSerializer,  # type: ignore[reportAttributeAccessIssue]
    DCATSerializer,  # type: ignore[reportAttributeAccessIssue]
    DublinCoreXMLSerializer,  # type: ignore[reportAttributeAccessIssue]
    GeoJSONSerializer,  # type: ignore[reportAttributeAccessIssue]
    MARCXMLSerializer,  # type: ignore[reportAttributeAccessIssue]
    SchemaorgJSONLDSerializer,  # type: ignore[reportAttributeAccessIssue]
    StringCitationSerializer,  # type: ignore[reportAttributeAccessIssue]
)
from oarepo_model.customizations import AddMetadataExport, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMCompleteExportsPreset(Preset):
    """Preset for exporting RDM-complete models."""

    modifies = ("exports",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddMetadataExport(
            code="jsonld",
            name=_("JSON-LD (schema.org)"),
            mimetype="application/ld+json",
            serializer=SchemaorgJSONLDSerializer(),
        )
        yield AddMetadataExport(
            code="csv-full",
            name=_("CSV (full)"),
            mimetype="text/vnd.inveniordm.v1.full+csv",
            serializer=CSVRecordSerializer(),
        )
        yield AddMetadataExport(
            code="csv-simple",
            name=_("CSV (simple)"),
            mimetype="text/vnd.inveniordm.v1.simple+csv",
            serializer=CSVRecordSerializer(
                csv_included_fields=[
                    "id",
                    "created",
                    "pids.doi.identifier",
                    "metadata.title",
                    "metadata.description",
                    "metadata.resource_type.title.en",
                    "metadata.publication_date",
                    "metadata.creators.person_or_org.type",
                    "metadata.creators.person_or_org.name",
                    "metadata.rights.id",
                ],
                collapse_lists=True,
            ),
        )
        yield AddMetadataExport(
            code="marcxml",
            name=_("MARCXML"),
            mimetype="application/marcxml+xml",
            serializer=MARCXMLSerializer(),
        )
        yield AddMetadataExport(
            code="csl",
            name=_("CSL JSON"),
            mimetype="application/vnd.citationstyles.csl+json",
            serializer=CSLJSONSerializer(),
        )
        yield AddMetadataExport(
            code="geojson",
            name=_("GeoJSON"),
            mimetype="application/vnd.geo+json",
            serializer=GeoJSONSerializer(),
        )
        yield AddMetadataExport(
            code="datacite-xml",
            name=_("DataCite XML"),
            mimetype="application/vnd.datacite.datacite+xml",
            serializer=DataCite43XMLSerializer(),
        )
        yield AddMetadataExport(
            code="datapackage",
            name=_("Data Package"),
            mimetype="application/vnd.datapackage.ld+json",
            serializer=DataPackageSerializer(),
        )
        yield AddMetadataExport(
            code="dublincore",
            name=_("Dublin Core XML"),
            mimetype="application/x-dc+xml",
            serializer=DublinCoreXMLSerializer(),
        )
        yield AddMetadataExport(
            code="citation",
            name=_("Citation"),
            mimetype="text/x-bibliography",
            serializer=StringCitationSerializer(url_args_retriever=csl_url_args_retriever),
        )
        yield AddMetadataExport(
            code="bibtex",
            name=_("BibTeX"),
            mimetype="application/x-bibtex",
            serializer=BibtexSerializer(),
        )
        yield AddMetadataExport(
            code="dcat",
            name=_("DCAT XML"),
            mimetype="application/dcat+xml",
            serializer=DCATSerializer(),
        )
