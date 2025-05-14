import os
from datetime import datetime
from unittest import mock

import arrow
import pytest
from dateutil import tz
from flask_principal import Identity, Need, UserNeed
from invenio_app.factory import create_api
from invenio_rdm_records.proxies import current_rdm_records_service
from modela.proxies import current_service as modela_service
from modelb.proxies import current_service as modelb_service
from modelc.proxies import current_service as modelc_service
from oarepo_runtime.services.custom_fields.mappings import prepare_cf_indices
from oarepo_workflows.base import Workflow
from oarepo_workflows.requests.policy import WorkflowRequestPolicy
from oarepo_workflows.services.permissions.workflow_permissions import (
    DefaultWorkflowPermissions,
)
from invenio_rdm_records.services.pids import providers
from invenio_oaiserver.views.server import blueprint
from oarepo_runtime.i18n import lazy_gettext as _
from oarepo_rdm.utils import refresh

pytest_plugins = [
    "pytest_oarepo.fixtures",
    "pytest_oarepo.records",
    "pytest_oarepo.users",
]

@pytest.fixture()
def app(app):
    if "invenio_oaiserver" not in app.blueprints:
        app.register_blueprint(blueprint)
    yield app

@pytest.fixture(scope="module")
def extra_entry_points():
    """Register extra entry point."""
    return {
        "invenio.modela.response_handlers": [
            "modela_oaidc_handler = tests.handlers:modela_handler"
        ],
        "invenio.modelb.response_handlers": [
            "modelb_oaidc_handler = tests.handlers:modelb_handler"
        ],
        "invenio.modelc.response_handlers": [
            "modelc_oaidc_handler = tests.handlers:modelc_handler"
        ]
    }


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return create_api


@pytest.fixture(scope="module", autouse=True)
def location(location):
    return location


@pytest.fixture(autouse=True)
def vocab_cf(vocab_cf):
    return vocab_cf


@pytest.fixture(scope="module")
def identity_simple():
    """Simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method="system_role", value="any_user"))
    i.provides.add(Need(method="system_role", value="authenticated_user"))
    return i


@pytest.fixture()
def rdm_records_service():
    return current_rdm_records_service


@pytest.fixture()
def workflow_data():
    return {"parent": {"workflow": "default"}}


WORKFLOWS = {
    "default": Workflow(
        label=_("Default workflow"),
        permission_policy_cls=DefaultWorkflowPermissions,
        request_policy_cls=WorkflowRequestPolicy,
    ),
}


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
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
    app_config["GLOBAL_SEARCH_MODELS"] = [
        {
            "model_service": "modela.services.records.service.ModelaService",
            "service_config": "modela.services.records.config.ModelaServiceConfig",
        },
        {
            "model_service": "modelb.services.records.service.ModelbService",
            "service_config": "modelb.services.records.config.ModelbServiceConfig",
        },
        {
            "model_service": "modelc.services.records.service.ModelcService",
            "service_config": "modelc.services.records.config.ModelcServiceConfig",
        },
    ]
    app_config["SITE_API_URL"] = "http://localhost"
    # app_config["SQLALCHEMY_ECHO"] = True
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
        {  # hack to avoid pool_timeout set in invenio_app_rdm
            "pool_pre_ping": False,
            "pool_recycle": 3600,
        },
    )
    app_config["REST_CSRF_ENABLED"] = False

    app_config["APP_RDM_ROUTES"] = {
        "record_detail": "/records/<pid_value>",
        "record_file_download": "/records/<pid_value>/files/<path:filename>",
    }

    app_config["WORKFLOWS"] = WORKFLOWS

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
    app_config["OAISERVER_RECORD_SETS_FETCHER"] = "oarepo_rdm.oai.percolator:find_sets_for_record"
    app_config["OAISERVER_RECORD_LIST_SETS_FETCHER"] = "oarepo_rdm.oai.percolator:sets_search_all"
    app_config["OAISERVER_ID_PREFIX"] = "oaioaioai"
    app_config["OAISERVER_NEW_PERCOLATOR_FUNCTION"] = "oarepo_rdm.oai.percolator:_new_percolator"
    app_config["OAISERVER_DELETE_PERCOLATOR_FUNCTION"] = "oarepo_rdm.oai.percolator:_delete_percolator"
    app_config["RDM_MODELS"] = [{ #todo this is explicit due to ui; is there a reason to not merge missing attributes in model ext?
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
            }
    ]

    app_config["RECORDS_REST_ENDPOINTS"] = (
        []
    )  # rule /records/<pid(recid):pid_value> is in race condition with
    # /records/<pid_value> from rdm and PIDConverter in it breaks record resolution due to use recid pid type
    app_config["RDM_MODELS"] = [{  # todo this is explicit due to ui; is there a reason to not merge missing attributes in model ext?
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
        }
    ]
    # /records/<pid_value> from rdm and PIDConverter in it breaks record resolution due to use recid pid type]
    app_config["SEARCH_INDEX_PREFIX"] = "nr_docs-"
    return app_config


@pytest.fixture()
def custom_fields():
    prepare_cf_indices()


# from invenio_rdm_records
@pytest.fixture()
def embargoed_files_record(rdm_records_service, identity_simple, workflow_data):
    def _record(records_service):
        today = arrow.utcnow().date().isoformat()
        # Add embargo to record
        with mock.patch("arrow.utcnow") as mock_arrow:
            data = {
                "metadata": {"title": "aaaaa", "adescription": "jej"},
                "files": {"enabled": False},
                "access": {
                    "record": "public",
                    "files": "restricted",
                    "status": "embargoed",
                    "embargo": dict(active=True, until=today, reason=None),
                },
                **workflow_data,
            }

            # We need to set the current date in the past to pass the validations
            mock_arrow.return_value = arrow.get(datetime(1954, 9, 29), tz.gettz("UTC"))
            draft = records_service.create(identity_simple, data)
            record = rdm_records_service.publish(id_=draft.id, identity=identity_simple)

            refresh(records_service.config.record_cls.index)
            refresh(records_service.config.draft_cls.index)

            # Recover current date
            mock_arrow.return_value = arrow.get(datetime.utcnow())
        return record

    return _record

@pytest.fixture(scope="function")
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

