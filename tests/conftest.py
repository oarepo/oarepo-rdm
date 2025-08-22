#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
import base64
import os
from datetime import UTC, datetime
from unittest import mock

import arrow
import pytest
from flask_principal import Identity, Need, UserNeed
from flask_security import login_user
from invenio_accounts.testutils import login_user_via_session
from invenio_app.factory import create_api
from invenio_i18n import _
from invenio_oaiserver.views.server import blueprint
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.records.api import RDMRecord
from invenio_rdm_records.services.pids import providers
from sqlalchemy.exc import IntegrityError

# pytest_plugins = [
# "pytest_oarepo.fixtures",
# "pytest_oarepo.records",
# "pytest_oarepo.users",
# ]


@pytest.fixture
def app(app):
    if "invenio_oaiserver" not in app.blueprints:
        app.register_blueprint(blueprint)
    return app


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return create_api


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
                "title": {"type": "fulltext+keyword", "required": True},
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


@pytest.fixture(scope="module")
def app_config(app_config, model_a, model_b, model_c):
    """Mimic an instance's configuration."""
    model_a.register()
    model_b.register()
    model_c.register()

    app_config["JSONSCHEMAS_HOST"] = "localhost"
    app_config["RECORDS_REFRESOLVER_CLS"] = (
        "invenio_records.resolver.InvenioRefResolver"
    )
    app_config["RECORDS_REFRESOLVER_STORE"] = (
        "invenio_jsonschemas.proxies.current_refresolver_store"
    )
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

    app_config["RDM_PERSISTENT_IDENTIFIER_PROVIDERS"] = [
        providers.OAIPIDProvider(
            "oai",
            label=_("OAI ID"),
        ),
    ]
    app_config["RDM_PERSISTENT_IDENTIFIERS"] = {
        "oai": {
            "providers": ["oai"],
            "required": True,
            "label": _("OAI"),
            "is_enabled": providers.OAIPIDProvider.is_enabled,
        },
    }

    app_config["OAISERVER_REPOSITORY_NAME"] = "Some thesis repository."
    app_config["OAISERVER_RECORD_INDEX"] = "modela,modelb,modelc"
    app_config["OAISERVER_CREATED_KEY"] = "created"
    app_config["OAISERVER_LAST_UPDATE_KEY"] = "updated"
    app_config["OAISERVER_RECORD_CLS"] = "invenio_rdm_records.records.api:RDMRecord"
    app_config["OAISERVER_SEARCH_CLS"] = "invenio_rdm_records.oai:OAIRecordSearch"
    app_config["OAISERVER_ID_FETCHER"] = "invenio_rdm_records.oai:oaiid_fetcher"
    app_config["OAISERVER_GETRECORD_FETCHER"] = "oarepo_rdm.oai.record:get_record"
    from oarepo_rdm.oai.config import OAIServerMetadataFormats

    app_config["OAISERVER_METADATA_FORMATS"] = OAIServerMetadataFormats()
    app_config["OAISERVER_RECORD_SETS_FETCHER"] = (
        "oarepo_rdm.oai.percolator:find_sets_for_record"
    )
    app_config["OAISERVER_RECORD_LIST_SETS_FETCHER"] = (
        "oarepo_rdm.oai.percolator:sets_search_all"
    )
    app_config["OAISERVER_ID_PREFIX"] = "oaioaioai"
    app_config["OAISERVER_NEW_PERCOLATOR_FUNCTION"] = (
        "oarepo_rdm.oai.percolator:_new_percolator"
    )
    app_config["OAISERVER_DELETE_PERCOLATOR_FUNCTION"] = (
        "oarepo_rdm.oai.percolator:_delete_percolator"
    )

    app_config["RECORDS_REST_ENDPOINTS"] = (
        []
    )  # rule /records/<pid(recid):pid_value> is in race condition with
    # /records/<pid_value> from rdm and PIDConverter in it breaks record resolution due to use recid pid type
    app_config["RDM_MODELS"] = [
        {  # TODO: this is explicit due to ui; is there a reason to not merge missing attributes in model ext?
            "service_id": "modela",
            # deprecated
            "model_service": "modela.services.records.service.ModelaService",
            # deprecated
            "service_config": "modela.services.records.config.ModelaServiceConfig",
            "api_service": "modela.services.records.service.ModelaService",
            "api_service_config": "modela.services.records.config.ModelaServiceConfig",
            "api_resource": "modela.resources.records.resource.ModelaResource",
            "api_resource_config": (
                "modela.resources.records.config.ModelaResourceConfig"
            ),
            "ui_resource_config": "tests.ui.modela.ModelaUIResourceConfig",
            "record_cls": "modela.records.api.ModelaRecord",
            "pid_type": "modela",
            "draft_cls": "modela.records.api.ModelaDraft",
        },
        {
            "service_id": "modelb",
            # deprecated
            "model_service": "modelb.services.records.service.ModelbService",
            # deprecated
            "service_config": "modelb.services.records.config.ModelbServiceConfig",
            "api_service": "modelb.services.records.service.ModelbService",
            "api_service_config": "modelb.services.records.config.ModelbServiceConfig",
            "api_resource": "modelb.resources.records.resource.ModelbResource",
            "api_resource_config": (
                "modelb.resources.records.config.ModelbResourceConfig"
            ),
            "ui_resource_config": "tests.ui.modelb.ModelbUIResourceConfig",
            "record_cls": "modelb.records.api.ModelbRecord",
            "pid_type": "modelb",
            "draft_cls": "modelb.records.api.ModelbDraft",
        },
        {
            "service_id": "modelc",
            # deprecated
            "model_service": "modelc.services.records.service.ModelcService",
            # deprecated
            "service_config": "modelc.services.records.config.ModelcServiceConfig",
            "api_service": "modelc.services.records.service.ModelcService",
            "api_service_config": "modelc.services.records.config.ModelcServiceConfig",
            "api_resource": "modelc.resources.records.resource.ModelcResource",
            "api_resource_config": (
                "modelc.resources.records.config.ModelcResourceConfig"
            ),
            "ui_resource_config": "tests.ui.modelc.ModelcUIResourceConfig",
            "record_cls": "modelc.records.api.ModelcRecord",
            "pid_type": "modelc",
            "draft_cls": "modelc.records.api.ModelcDraft",
        },
    ]
    # /records/<pid_value> from rdm and PIDConverter in it breaks record resolution due to use recid pid type]
    app_config["SEARCH_INDEX_PREFIX"] = "nr_docs-"
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


@pytest.fixture
def search_clear_percolators():
    """Clear search indices after test finishes (function scope).

    Scope: function

    This fixture rollback any changes performed to the indexes during a test,
    in order to leave search in a clean state for the next test.
    """
    from invenio_search import current_search_client

    yield
    indices = current_search_client.indices.get_alias("").keys()
    percolator_indices = [index for index in indices if index.endswith("percolators")]
    for perc in percolator_indices:
        current_search_client.indices.delete(perc)


#
#
#
#
#
# TODO: use pytest-oarepo instead of this
@pytest.fixture
def password():
    """Password fixture."""
    return base64.b64encode(os.urandom(16)).decode("utf-8")


def _create_user(user_fixture, app, db) -> None:
    """Create users, reusing it if it already exists."""
    try:
        user_fixture.create(app, db)
    except IntegrityError:
        datastore = app.extensions["security"].datastore
        user_fixture._user = datastore.get_user_by_email(  # noqa: SLF001
            user_fixture.email
        )
        user_fixture._app = app  # noqa: SLF001
        app.logger.info("skipping creation of %s, already existing", user_fixture.email)


@pytest.fixture
def users(app, db, UserFixture, password):
    """Predefined user fixtures."""
    user1 = UserFixture(
        email="user1@example.org",
        password=password,
        active=True,
        confirmed=True,
        user_profile={
            "affiliations": "CERN",
        },
    )
    _create_user(user1, app, db)

    user2 = UserFixture(
        email="user2@example.org",
        password=password,
        username="beetlesmasher",
        active=True,
        confirmed=True,
        user_profile={
            "affiliations": "CERN",
        },
    )
    _create_user(user2, app, db)

    user3 = UserFixture(
        email="user3@example.org",
        password=password,
        username="beetlesmasherXXL",
        user_profile={
            "full_name": "Maxipes Fik",
            "affiliations": "CERN",
        },
        active=True,
        confirmed=True,
    )
    _create_user(user3, app, db)

    user4 = UserFixture(
        email="user4@example.org",
        password=password,
        username="african",
        preferences={
            "timezone": "Africa/Dakar",  # something without daylight saving time; +0.0
        },
        user_profile={
            "affiliations": "CERN",
        },
        active=True,
        confirmed=True,
    )
    _create_user(user4, app, db)

    user5 = UserFixture(
        email="user5@example.org",
        password=password,
        username="mexican",
        preferences={
            "timezone": "America/Mexico_City",  # something without daylight saving time
        },
        user_profile={
            "affiliations": "CERN",
        },
        active=True,
        confirmed=True,
    )
    _create_user(user5, app, db)

    return [user1, user2, user3, user4, user5]


class LoggedClient:
    def __init__(self, client, user_fixture):
        self.client = client
        self.user_fixture = user_fixture

    def _login(self):
        login_user(self.user_fixture.user, remember=True)
        login_user_via_session(self.client, email=self.user_fixture.email)

    def post(self, *args, **kwargs):
        self._login()
        return self.client.post(*args, **kwargs)

    def get(self, *args, **kwargs):
        self._login()
        return self.client.get(*args, **kwargs)

    def put(self, *args, **kwargs):
        self._login()
        return self.client.put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._login()
        return self.client.delete(*args, **kwargs)


@pytest.fixture
def logged_client(client):
    def _logged_client(user):
        return LoggedClient(client, user)

    return _logged_client
