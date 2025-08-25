#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import base64
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from unittest import mock

import arrow
import pytest
from flask_principal import Identity, Need, UserNeed
from flask_security import login_user
from invenio_accounts.testutils import login_user_via_session
from invenio_app.factory import create_api
from invenio_oaiserver.views.server import blueprint
from invenio_rdm_records.proxies import current_rdm_records_service
from sqlalchemy.exc import IntegrityError

if TYPE_CHECKING:
    from collections.abc import Callable

    from invenio_accounts.models import User
    from invenio_rdm_records.records.api import RDMRecord

# TODO: add pytest-oarepo and remove some of the fixtures below


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

    app_config["OAISERVER_REPOSITORY_NAME"] = "Some thesis repository."

    app_config["SEARCH_INDEX_PREFIX"] = "test-"

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
def search(search):
    from oarepo_runtime.services.records.mapping import update_all_records_mappings

    from oarepo_rdm.oai.percolator import init_percolators

    update_all_records_mappings()
    init_percolators()


@pytest.fixture
def percolators():
    from oarepo_rdm.oai.percolator import init_percolators

    init_percolators()


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
def users(app, db, UserFixture, password):  # noqa: N803 # as it is a fixture name
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
    """Logged client for testing."""

    def __init__(self, client, user_fixture):
        """Initialize the logged client."""
        self.client = client
        self.user_fixture = user_fixture

    def _login(self) -> None:
        """Perform login."""
        login_user(self.user_fixture.user, remember=True)
        login_user_via_session(self.client, email=self.user_fixture.email)

    def post(self, *args: Any, **kwargs: Any) -> Any:
        """Send a POST request with authentication."""
        self._login()
        return self.client.post(*args, **kwargs)

    def get(self, *args: Any, **kwargs: Any) -> Any:
        """Send a GET request with authentication."""
        self._login()
        return self.client.get(*args, **kwargs)

    def put(self, *args: Any, **kwargs: Any) -> Any:
        """Send a PUT request with authentication."""
        self._login()
        return self.client.put(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> Any:
        """Send a DELETE request with authentication."""
        self._login()
        return self.client.delete(*args, **kwargs)


@pytest.fixture
def logged_client(client) -> Callable[[User], LoggedClient]:
    def _logged_client(user) -> LoggedClient:
        return LoggedClient(client, user)

    return _logged_client


@pytest.fixture
def oai_prefix(app):
    return f"oai:{app.config['OAISERVER_ID_PREFIX']}:"
