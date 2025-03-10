from __future__ import annotations

from typing import TYPE_CHECKING

from invenio_rdm_records import InvenioRDMRecords
from invenio_rdm_records.oaiserver.services.services import OAIPMHServerService
from invenio_rdm_records.services import (
    CommunityRecordsService,
    IIIFService,
    RDMRecordService,
    RecordAccessService,
    RecordRequestsService,
)
from invenio_rdm_records.services.communities.service import RecordCommunitiesService
from invenio_rdm_records.services.community_inclusion.service import (
    CommunityInclusionService,
)
from invenio_rdm_records.services.files.service import RDMFileService
from invenio_rdm_records.services.pids.manager import PIDManager
from invenio_rdm_records.services.pids.service import PIDsService
from invenio_records_resources.records.systemfields import IndexField
from invenio_records_resources.records.systemfields.pid import PIDField
from oarepo_global_search.proxies import current_global_search

from oarepo_rdm.records.systemfields.pid import (
    OARepoDraftPIDFieldContext,
    OARepoPIDFieldContext,
)
from oarepo_rdm.services.service import OARepoRDMService

if TYPE_CHECKING:
    from flask import Flask


class InvenioRDMRecords(InvenioRDMRecords):
    """Invenio-RDM-Records extension."""

    def init_services(self, app):
        """Initialize services."""
        service_configs = self.service_configs(app)

        # Services
        self.records_service = OARepoRDMService(
            service_configs.record,
            files_service=RDMFileService(service_configs.file),
            draft_files_service=RDMFileService(service_configs.file_draft),
            access_service=RecordAccessService(service_configs.record),
            pids_service=PIDsService(service_configs.record, PIDManager),
            # review_service=ReviewService(service_configs.record),
        )

        self.records_media_files_service = RDMRecordService(
            service_configs.record_with_media_files,
            files_service=RDMFileService(service_configs.media_file),
            draft_files_service=RDMFileService(service_configs.media_file_draft),
            pids_service=PIDsService(service_configs.record, PIDManager),
        )

        self.iiif_service = IIIFService(
            records_service=self.records_service, config=None
        )

        self.record_communities_service = RecordCommunitiesService(
            config=service_configs.record_communities,
        )

        self.community_records_service = CommunityRecordsService(
            config=service_configs.community_records,
        )

        self.community_inclusion_service = CommunityInclusionService()
        self.record_requests_service = RecordRequestsService(
            config=service_configs.record_requests
        )

        self.oaipmh_server_service = OAIPMHServerService(
            config=service_configs.oaipmh_server,
        )


def api_finalize_app(app: Flask) -> None:
    """Finalize app."""
    finalize_app(app)

    rdm = app.extensions["invenio-rdm-records"]
    sregistry = app.extensions["invenio-records-resources"].registry

    sregistry.register(rdm.records_service, service_id="records")
    sregistry.register(rdm.records_service.files, service_id="files")
    sregistry.register(rdm.records_service.draft_files, service_id="draft-files")


def finalize_app(app: Flask) -> None:
    """Finalize app."""
    from invenio_rdm_records.records.api import RDMDraft, RDMRecord

    RDMRecord.pid = PIDField(context_cls=OARepoPIDFieldContext)
    RDMDraft.pid = PIDField(context_cls=OARepoDraftPIDFieldContext)
    RDMRecord.index = IndexField(
        None, search_alias=current_global_search.indices
    )  # todo - should be just published indices, not all
    RDMDraft.index = IndexField(None, search_alias=current_global_search.indices)
