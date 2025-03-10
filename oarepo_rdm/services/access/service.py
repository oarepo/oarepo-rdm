from invenio_rdm_records.services.access.service import RecordAccessService
from datetime import datetime, timedelta

import arrow
from flask import current_app
from flask_login import current_user
from invenio_access.permissions import authenticated_user, system_identity
from invenio_drafts_resources.services.records import RecordService
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_i18n import lazy_gettext as _
from invenio_notifications.services.uow import NotificationOp
from invenio_records_resources.services.errors import PermissionDeniedError
from invenio_records_resources.services.records.schema import ServiceSchemaWrapper
from invenio_records_resources.services.uow import unit_of_work
from invenio_requests.proxies import current_requests_service
from invenio_search.engine import dsl
from invenio_users_resources.proxies import current_user_resources
from marshmallow.exceptions import ValidationError
from sqlalchemy.orm.exc import NoResultFound

from invenio_rdm_records.notifications.builders import (
    GrantUserAccessNotificationBuilder,
    GuestAccessRequestTokenCreateNotificationBuilder,
)

from invenio_rdm_records.requests.access import AccessRequestToken, GuestAccessRequest, UserAccessRequest
from invenio_rdm_records.secret_links.errors import InvalidPermissionLevelError
from invenio_rdm_records.services.decorators import groups_enabled
from invenio_rdm_records.services.errors import AccessRequestExistsError, GrantExistsError
from invenio_rdm_records.services.results import GrantSubjectExpandableField
from oarepo_rdm.requests.guest_access import OARepoGuestAccessRequest, OARepoUserAccessRequest


class OARepoRecordAccessService(RecordAccessService):

    @unit_of_work()
    def create_guest_access_request(self, identity, token, expand=False, uow=None):
        """Use the guest access request token to create an access request."""
        # Permissions
        if authenticated_user in identity.provides:
            raise PermissionDeniedError("request_guest_access")

        access_token = AccessRequestToken.get_by_token(token)
        if access_token is None:
            return

        access_token_data = access_token.to_dict()
        record = self.record_cls.pid.resolve(access_token_data["record_pid"])

        # Detect duplicate requests
        existing_access_request = self._exists(
            created_by={"email": access_token.email},
            record_id=access_token.record_pid,
            request_type=OARepoGuestAccessRequest.type_id,
        )

        if existing_access_request:
            raise AccessRequestExistsError(existing_access_request["id"])
        data = {
            "payload": {
                "permission": "view",
                "email": access_token_data["email"],
                "full_name": access_token_data["full_name"],
                "token": access_token_data["token"],
                "message": access_token_data.get("message", ""),
                "consent_to_share_personal_data": access_token_data.get(
                    "consent_to_share_personal_data"
                ),
                "secret_link_expiration": str(
                    record.parent.access.settings.secret_link_expiration
                ),
            }
        }

        receiver = None
        record_owner = record.parent.access.owner.resolve()
        if record_owner:
            receiver = record_owner

        access_token.delete()
        request = current_requests_service.create(
            system_identity,
            data,
            OARepoGuestAccessRequest, # todo - this is the only change needed - for now the only change in request type is that we need it work with our topic types
            receiver,
            creator=data["payload"]["email"],
            topic=record,
            expires_at=None,
            expand=expand,
            uow=uow,
        )

        message = data["payload"].get("message")
        comment = None
        if message:
            comment = {"payload": {"content": message}}

        return current_requests_service.execute_action(
            identity,
            request.id,
            "submit",
            data=comment,
            uow=uow,
        )

    @unit_of_work()
    def create_user_access_request(self, identity, id_, data, expand=False, uow=None):
        """Create a user access request for the given record."""
        record = self.record_cls.pid.resolve(id_)

        # Permissions
        # fail early if record fully restricted
        self.require_permission(identity, "read", record=record)

        can_read_files = self.check_permission(identity, "read_files", record=record)

        if can_read_files:
            raise PermissionDeniedError(
                "You already have access to files of this record."
            )

        existing_access_request = self._exists(
            created_by={"user": str(identity.id)},
            record_id=id_,
            request_type=UserAccessRequest.type_id,
        )

        if existing_access_request:
            raise AccessRequestExistsError(existing_access_request["id"])

        data, __ = self.schema_request_access.load(
            data, context={"identity": identity}, raise_errors=True
        )

        data = {"payload": data}

        # Determine the request's receiver
        receiver = None
        record_owner = record.parent.access.owner.resolve()
        if record_owner:
            receiver = record_owner

        request = current_requests_service.create(
            identity,
            data,
            OARepoUserAccessRequest,
            receiver,
            topic=record,
            expires_at=None,
            expand=expand,
            uow=uow,
        )

        message = data["payload"].get("message")
        comment = None
        if message:
            comment = {
                "payload": {
                    "content": message,
                }
            }
        return current_requests_service.execute_action(
            identity,
            request.id,
            "submit",
            data=comment,
            uow=uow,
        )
