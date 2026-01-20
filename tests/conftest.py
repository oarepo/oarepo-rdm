#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import mock
from unittest.mock import MagicMock

import arrow
import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_access.permissions import system_identity
from invenio_app.factory import create_app as _create_app
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_vocabularies.proxies import current_service as current_vocabularies_service
from oarepo_model.customizations import AddToList

if TYPE_CHECKING:
    from invenio_rdm_records.records.api import RDMRecord


pytest_plugins = [
    "pytest_oarepo.fixtures",
    "pytest_oarepo.users",
    "pytest_oarepo.files",
    "pytest_oarepo.ui.fixtures",
]


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_app


@pytest.fixture(scope="module", autouse=True)
def location(location):
    return location


@pytest.fixture(scope="module")
def identity_simple():
    """Return simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method="system_role", value="any_user"))
    i.provides.add(Need(method="system_role", value="authenticated_user"))
    return i


@pytest.fixture
def rdm_records_service():
    return current_rdm_records_service


@pytest.fixture(scope="session")
def model_types():
    """Model types fixture."""
    # Define the model types used in the tests
    return {
        "Metadata": {
            "properties": {
                "title": {"type": "keyword", "required": True},
            }
        }
    }


@pytest.fixture(scope="session")
def model_a(model_types):
    from .models import modela

    return modela


@pytest.fixture(scope="session")
def model_b(model_types):
    from .models import modelb

    return modelb


@pytest.fixture(scope="session")
def model_c(model_types):
    from .models import modelc

    return modelc


@pytest.fixture(scope="session")
def finalization_called():
    return MagicMock()


@pytest.fixture(scope="session")
def rdm_model(model_types, finalization_called):
    from oarepo_model.api import model

    from oarepo_rdm.model.presets import rdm_minimal_preset

    ret = model(
        name="rdm_test",
        version="1.0.0",
        presets=[
            rdm_minimal_preset,
        ],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[
            AddToList("api_finalizers", finalization_called),
        ],
    )
    ret.register()
    return ret


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["JSONSCHEMAS_HOST"] = "localhost"
    app_config["RECORDS_REFRESOLVER_CLS"] = "invenio_records.resolver.InvenioRefResolver"
    app_config["RECORDS_REFRESOLVER_STORE"] = "invenio_jsonschemas.proxies.current_refresolver_store"
    app_config["RATELIMIT_AUTHENTICATED_USER"] = "200 per second"
    app_config["SEARCH_HOSTS"] = [
        {
            "host": os.environ.get("OPENSEARCH_HOST", "localhost"),
            "port": os.environ.get("OPENSEARCH_PORT", "9200"),
        }
    ]
    app_config["SITE_API_URL"] = "http://localhost"
    app_config["FILES_REST_STORAGE_CLASS_LIST"] = {
        "L": "Local",
        "F": "Fetch",
        "R": "Remote",
    }
    app_config["FILES_REST_DEFAULT_STORAGE_CLASS"] = "L"

    app_config["RDM_PERSISTENT_IDENTIFIERS"] = {}
    app_config["RDM_USER_MODERATION_ENABLED"] = False
    app_config["RDM_RECORDS_ALLOW_RESTRICTION_AFTER_GRACE_PERIOD"] = False
    app_config["RDM_ALLOW_METADATA_ONLY_RECORDS"] = True
    app_config["RDM_DEFAULT_FILES_ENABLED"] = False
    app_config["RDM_SEARCH_SORT_BY_VERIFIED"] = False

    app_config["SQLALCHEMY_ENGINE_OPTIONS"] = (
        {  # avoid pool_timeout set in invenio_app_rdm
            "pool_pre_ping": False,
            "pool_recycle": 3600,
        },
    )
    app_config["REST_CSRF_ENABLED"] = False

    app_config["OAISERVER_REPOSITORY_NAME"] = "Some thesis repository."

    app_config["SEARCH_INDEX_PREFIX"] = "test-"

    # if on macOS, we need to add homebrew path otherwise we'll have problems
    # with loading cairo-2
    if os.uname().sysname == "Darwin" and Path("/opt/homebrew/lib").exists():
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/lib"

    return app_config


# from invenio_rdm_records
@pytest.fixture
def embargoed_files_record(rdm_records_service, identity_simple):
    def _record(records_service) -> RDMRecord:
        # Add embargo to record
        with mock.patch("arrow.utcnow") as mock_arrow:
            data = {
                "metadata": {"title": "aaaaa", "adescription": "jej"},
                "files": {"enabled": False},
                "access": {
                    "record": "public",
                    "files": "restricted",
                    "status": "embargoed",
                    "embargo": {
                        "active": True,
                        "until": datetime.now(tz=UTC).date().isoformat(),
                        "reason": None,
                    },
                },
            }

            # We need to set the current date in the past to pass the validations
            mock_arrow.return_value = datetime(1954, 9, 29, tzinfo=UTC)
            draft = records_service.create(identity_simple, data)
            record = rdm_records_service.publish(id_=draft.id, identity=identity_simple)
            records_service.indexer.refresh()
            records_service.draft_indexer.refresh()
            # Recover current date
            mock_arrow.return_value = arrow.get(datetime.now(tz=UTC))
        return record

    return _record


@pytest.fixture(scope="module")
def extra_entry_points(model_a, model_b, model_c, rdm_model):
    """Extra entrypoints."""
    return {
        "invenio_base.blueprints": [
            "modela_ui = tests.models:create_modela_ui_blueprint",
        ],
    }


@pytest.fixture(scope="module")
def search(search):
    from oarepo_runtime.services.records.mapping import update_all_records_mappings

    from oarepo_rdm.oai.percolator import init_percolators

    update_all_records_mappings()
    init_percolators()


@pytest.fixture
def percolators():
    from oarepo_rdm.oai.percolator import init_percolators

    init_percolators()


@pytest.fixture
def required_rdm_metadata():
    return {
        "resource_type": {"id": "image-photo"},
        "creators": [
            {
                "person_or_org": {
                    "name": "Nielsen, Lars Holm",
                    "type": "personal",
                    "given_name": "Lars Holm",
                    "family_name": "Nielsen",
                    "identifiers": [
                        {
                            "scheme": "orcid",
                            "identifier": "0000-0001-8135-3489",
                        }
                    ],
                },
            }
        ],
        "title": "InvenioRDM",
        "publication_date": "2020-06-01",
    }


@pytest.fixture
def oai_prefix(app):
    return f"oai:{app.config['OAISERVER_ID_PREFIX']}:"


@pytest.fixture(scope="module")
def test_rdm_service(app):
    """Service instance."""
    return app.extensions["rdm_test"].records_service


@pytest.fixture(scope="module")
def test_rdm_draft_files_service(app):
    """Service instance."""
    return app.extensions["rdm_test"].draft_files_service


@pytest.fixture
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        "metadata": {"title": "Test"},
        "files": {
            "enabled": True,
        },
    }


@pytest.fixture
def vocab_fixtures():
    """Contributor role fixture."""
    current_vocabularies_service.create_type(system_identity, "contributorsroles", "v-ct")

    current_vocabularies_service.create(
        system_identity,
        {
            "type": "contributorsroles",
            "id": "editor",
            "title": {
                "en": "Editor",
                "cs": "Redaktor",
            },
        },
    )

    current_vocabularies_service.create_type(system_identity, "resourcetypes", "rsrct")

    current_vocabularies_service.create(
        system_identity,
        {
            "id": "image-photo",
            "props": {
                "csl": "graphic",
                "datacite_general": "Image",
                "datacite_type": "Photo",
                "openaire_resourceType": "25",
                "openaire_type": "dataset",
                "eurepo": "info:eu-repo/semantics/other",
                "schema.org": "https://schema.org/Photograph",
                "subtype": "image-photo",
                "type": "image",
                "marc21_type": "image",
                "marc21_subtype": "photo",
            },
            "icon": "chart bar outline",
            "title": {"en": "Photo"},
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
        },
    )

    current_vocabularies_service.indexer.refresh()
