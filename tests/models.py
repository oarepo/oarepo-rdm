#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from invenio_records_resources.services.records.facets import TermsFacet
from oarepo_model.api import model
from oarepo_model.presets.drafts import drafts_presets
from oarepo_model.presets.rdm import rdm_presets
from oarepo_model.presets.records_resources import records_resources_presets

modela = model(
    "modela",
    version="1.0.0",
    presets=[records_resources_presets, drafts_presets, rdm_presets],
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
    customizations=[],
)

modelb = model(
    "modelb",
    version="1.0.0",
    presets=[records_resources_presets, drafts_presets, rdm_presets],
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
    customizations=[],
)

modelc = model(
    "modelc",
    version="1.0.0",
    presets=[records_resources_presets, drafts_presets, rdm_presets],
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
    customizations=[],
)

assert (
    "metadata_adescription" not in modela.RecordServiceConfig.search.facets
), "Remove this assert when facets are supported in oarepo-model"

modela.RecordServiceConfig.search.facets["metadata_adescription"] = TermsFacet(
    field="metadata.adescription", label="A Description"
)
