from datetime import datetime, timedelta

from invenio_access.permissions import system_identity
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_notifications.services.uow import NotificationOp
from invenio_rdm_records.notifications.builders import (
    GuestAccessRequestAcceptNotificationBuilder,
)
from invenio_rdm_records.proxies import current_rdm_records_service as service
from invenio_rdm_records.requests.access.requests import (
    GuestAccessRequest,
    UserAccessRequest,
)
from invenio_requests import current_events_service
from invenio_requests.customizations import actions
from invenio_requests.customizations.event_types import CommentEventType
from oarepo_requests.types.ref_types import ModelRefTypes, ReceiverRefTypes


class OARepoGuestAcceptAction(actions.AcceptAction):
    """Accept action."""

    def execute(self, identity, uow):
        """Accept guest access request."""
        id_ = list(self.request.topic.reference_dict.values())[
            0
        ]  # needs to be changed bc invenio has hardcoded "record" as topic type
        record = service.read(id_=id_, identity=system_identity)
        payload = self.request["payload"]

        # NOTE: the description isn't translated because it can be changed later
        #       by the record owner
        data = {
            "permission": payload["permission"],
            "description": (
                f"Requested by guest: {payload['full_name']} ({payload['email']})"
            ),
            "origin": f"request:{self.request.id}",
        }

        # secret link will never expire if secret_link_expiration is empty
        days = int(payload["secret_link_expiration"])
        # TODO date calculation could be done elsewhere ?
        if days:
            data["expires_at"] = (
                (datetime.utcnow() + timedelta(days=days)).date().isoformat()
            )
        link = service.access.create_secret_link(identity, record.id, data)
        access_url = f"{record.links['self_html']}?token={link._link.token}"

        uow.register(
            ParentRecordCommitOp(
                record._record.parent, indexer_context=dict(service=service)
            )
        )
        uow.register(
            NotificationOp(
                GuestAccessRequestAcceptNotificationBuilder.build(
                    self.request, access_url=access_url
                )
            )
        )

        super().execute(identity, uow)

        confirmation_message = {
            "payload": {
                "content": 'Click <a href="{url}">here</a> to access the record.'.format(
                    url=access_url
                )
            }
        }
        current_events_service.create(
            system_identity,
            self.request.id,
            confirmation_message,
            CommentEventType,
            uow=uow,
            notify=False,
        )


class OARepoGuestAccessRequest(GuestAccessRequest):
    """"""

    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)
    allowed_receiver_ref_types = ReceiverRefTypes()

    available_actions = {
        **GuestAccessRequest.available_actions,
        "accept": OARepoGuestAcceptAction,
    }


class OARepoUserAccessRequest(UserAccessRequest):
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)
    allowed_receiver_ref_types = ReceiverRefTypes()
