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
from typing import TYPE_CHECKING, Any
from unittest import mock
from unittest.mock import MagicMock

import pytest
from invenio_access.permissions import system_identity
from invenio_app.factory import create_api
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.services.components import DefaultRecordsComponents
from invenio_records_resources.services.records.components.base import ServiceComponent
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
    return create_api


@pytest.fixture(scope="module", autouse=True)
def location(location):
    return location


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


class MockReviewInRDMServiceComponent(ServiceComponent):
    """Add review service component."""

    def create_review(self, identity, **kwargs: Any):  # noqa: ARG002
        """Mock create review."""
        print("review created in original rdm service component")  # noqa T201


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

    app_config["RDM_RECORDS_SERVICE_COMPONENTS"] = (
        *DefaultRecordsComponents,
        MockReviewInRDMServiceComponent,
    )
    # Disable invenio_records_ui routes - we use our own record_detail view
    app_config["RECORDS_UI_ENDPOINTS"] = {}
    app_config["SITE_API_URL"] = ""

    # if on macOS, we need to add homebrew path otherwise we'll have problems
    # with loading cairo-2
    if os.uname().sysname == "Darwin" and Path("/opt/homebrew/lib").exists():
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/lib"

    return app_config


# from invenio_rdm_records
@pytest.fixture
def unlifted_expired_embargoed_files_record(rdm_records_service, identity_simple):
    def _record(records_service) -> RDMRecord:
        with mock.patch("invenio_rdm_records.services.schemas.access.datetime") as mock_dt:
            # invenio validates inside invenio_rdm_records.services.schemas.access.EmbargoSchema that `until` is
            # in the future. Because embargo is evaluated on daily basis we must pretend that actual time is in the
            # past in order for the schema check to pass.
            # Note that all other datetime fields on the record contain current date (so inconsistent with the date
            # below) but no test that uses this embargoed file record uses those dates
            mock_dt.now.return_value = datetime(1954, 9, 29, tzinfo=UTC)
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
            draft = records_service.create(identity_simple, data)
            record = rdm_records_service.publish(id_=draft.id, identity=identity_simple)
            records_service.indexer.refresh()
            records_service.draft_indexer.refresh()
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
    """Create vocabulary types required for VocabulariesOptions.dump()."""
    # contributorsroles
    current_vocabularies_service.create_type(system_identity, "contributorsroles", "v-ct")
    current_vocabularies_service.create(
        system_identity,
        {
            "type": "contributorsroles",
            "id": "editor",
            "title": {"en": "Editor", "cs": "Redaktor"},
        },
    )

    # resourcetypes
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

    # titletypes
    current_vocabularies_service.create_type(system_identity, "titletypes", "tttyp")
    current_vocabularies_service.create(
        system_identity,
        {
            "type": "titletypes",
            "id": "alternative-title",
            "title": {"en": "Alternative title"},
        },
    )

    # creatorsroles
    current_vocabularies_service.create_type(system_identity, "creatorsroles", "crrol")
    current_vocabularies_service.create(
        system_identity,
        {"type": "creatorsroles", "id": "author", "title": {"en": "Author"}},
    )

    # descriptiontypes
    current_vocabularies_service.create_type(system_identity, "descriptiontypes", "dstyp")
    current_vocabularies_service.create(
        system_identity,
        {"type": "descriptiontypes", "id": "abstract", "title": {"en": "Abstract"}},
    )

    # datetypes
    current_vocabularies_service.create_type(system_identity, "datetypes", "dttyp")
    current_vocabularies_service.create(
        system_identity,
        {"type": "datetypes", "id": "accepted", "title": {"en": "Accepted"}},
    )

    # relationtypes
    current_vocabularies_service.create_type(system_identity, "relationtypes", "relty")
    current_vocabularies_service.create(
        system_identity,
        {"type": "relationtypes", "id": "cites", "title": {"en": "Cites"}},
    )

    # removalreasons
    current_vocabularies_service.create_type(system_identity, "removalreasons", "rmrsn")
    current_vocabularies_service.create(
        system_identity,
        {
            "type": "removalreasons",
            "id": "spam",
            "title": {"en": "Spam"},
            "tags": ["deletion-request"],
        },
    )

    current_vocabularies_service.indexer.refresh()
