import copy
import io
import re
import urllib
from modela.proxies import current_service as modela_service
from flask_principal import UserNeed
from invenio_access.permissions import (
    Identity,
    any_user,
    authenticated_user
)
from invenio_requests.proxies import current_requests_service

from invenio_rdm_records.proxies import current_rdm_records_service as service
from invenio_rdm_records.requests.access import AccessRequestTokenNeed


def test_simple_guest_access_request_flow(app, client, users, minimal_record):
    """Test a the simple guest-based access request flow."""
    with app.extensions["mail"].record_messages() as outbox:
        # Log in a user (whose ID we need later)
        record_owner = users[0]
        identity = Identity(record_owner.user.id)
        identity.provides.add(any_user)
        identity.provides.add(authenticated_user)
        identity.provides.add(UserNeed(record_owner.user.id))
        guest_identity = Identity(None)
        guest_identity.provides.add(any_user)

        # Create a public record with some restricted files
        record_json = copy.deepcopy(minimal_record)
        record_json["files"] = {"enabled": True}
        record_json["access"]["record"] = "public"
        record_json["access"]["files"] = "restricted"

        draft = service.create(identity=identity, data=record_json)
        service.draft_files.init_files(identity, draft.id, data=[{"key": "test.txt"}])
        service.draft_files.set_file_content(
            identity, draft.id, "test.txt", io.BytesIO(b"test file")
        )
        service.draft_files.commit_file(identity, draft.id, "test.txt")
        record = service.publish(identity=identity, id_=draft.id)

        # Make sure there is no secret link for the record yet
        assert not record._obj.parent.access.links
        modela_service.config.record_cls.index.refresh()

        # The user can access the record, but not the files
        #assert client.get(f"/records/{record.id}").status_code == 200 # todo discuss how to correctly use PIDConverter with multiple models
        #assert client.get(f"/records/{record.id}/files").status_code == 403
        #assert (
       #     client.get(f"/records/{record.id}/files/test.txt/content").status_code
        #    == 403
        #)



        # The guest creates an access request
        response = client.post(
            f"/records/{record.id}/access/request",
            json={
                "message": "This is not spam!",
                "email": "idle@montypython.com",
                "full_name": "Eric Idle",
                "consent_to_share_personal_data": "true",
            },
        )
        assert response.status_code == 200
        assert len(outbox) == 1
        verify_email_message = outbox[0]

        # Fetch the link from the response & parse the access request token
        link_regex = re.compile(r"(https?://.*?)\s?$")
        match = link_regex.search(str(verify_email_message.body))
        assert match
        verification_url = match.group(1)
        parsed = urllib.parse.urlparse(verification_url)
        args = {k: v for k, v in [kv.split("=") for kv in parsed.query.split("&")]}
        assert "access_request_token" in args
        token = args["access_request_token"]
        guest_identity.provides.add(AccessRequestTokenNeed(token))

        # Create the access request from the token
        # NOTE: we're not going through a `ui_app.test_client` here because that would
        #       require us to build the frontend assets to get a `manifest.json`
        request = service.access.create_guest_access_request(
            identity=guest_identity, token=args["access_request_token"]
        )

        assert len(outbox) == 2
        submit_message = outbox[1]
        # TODO: update to `req["links"]["self_html"]` when addressing https://github.com/inveniosoftware/invenio-rdm-records/issues/1327
        assert "/me/requests/{}".format(request.id) in submit_message.html

        # Accept the request
        # This is expected to send out another email, containing the new secret link
        current_requests_service.execute_action(identity, request.id, "accept", data={})
        assert len(outbox) == 3
        success_message = outbox[2]
        match = link_regex.search(str(success_message.body))
        assert match
        access_url = match.group(1)
        parsed = urllib.parse.urlparse(access_url)
        args = {k: v for k, v in [kv.split("=") for kv in parsed.query.split("&")]}
        assert "token" in args

        # The user can now access the record and its files via the secret link
        assert (
            client.get(f"/records/{record.id}?token={args['token']}").status_code == 200
        )
        assert (
            client.get(f"/records/{record.id}/files?token={args['token']}").status_code
            == 200
        )
        assert (
            client.get(
                f"/records/{record.id}/files/test.txt/content?token={args['token']}"
            ).status_code
            == 200
        )

        # Make sure that the secret link for the record was created
        record = service.read(identity=identity, id_=record.id)
        secret_links = record._obj.parent.access.links
        assert len(secret_links) == 1
        secret_link = secret_links[0].resolve()
        assert secret_link.token == args["token"]
        assert secret_link.permission_level == "view"
        assert secret_link.origin == f"request:{request.id}"