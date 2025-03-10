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
from flask_security import login_user
from invenio_access.permissions import (
    Identity,
    any_user,
    authenticated_user,
    system_identity,
)
from invenio_accounts.proxies import current_datastore
from invenio_accounts.testutils import login_user_via_session

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
        assert client.get(f"/modela/{record.id}").status_code == 200 # todo discuss how to correctly use PIDConverter with multiple models
        assert client.get(f"/modela/{record.id}/files").status_code == 403
        assert (
            client.get(f"/modela/{record.id}/files/test.txt/content").status_code
            == 403
        )



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

        assert len(outbox) == 3 # GuestAccessRequestSubmittedNotificationBuilder is not dummy unlike in invenio
        submit_message = outbox[1]
        assert "/me/requests/{}".format(request.id) in submit_message.html

        # Accept the request
        # This is expected to send out another email, containing the new secret link
        current_requests_service.execute_action(identity, request.id, "accept", data={})
        assert len(outbox) == 4
        success_message = outbox[3]
        match = link_regex.search(str(success_message.body))
        assert match
        access_url = match.group(1)
        parsed = urllib.parse.urlparse(access_url)
        args = {k: v for k, v in [kv.split("=") for kv in parsed.query.split("&")]}
        assert "token" in args

        # The user can now access the record and its files via the secret link
        assert client.get(f"/modela/{record.id}/files").status_code == 403
        assert client.get(f"/modela/{record.id}?token={args['token']}").status_code == 200
        assert client.get(f"/modela/{record.id}/files").status_code == 200 # todo is this correct - is it ok that the token is cached somewhere?
        assert client.get(f"/modela/{record.id}/files?token={args['token']}").status_code == 200
        assert client.get(f"/modela/{record.id}/files/test.txt/content?token={args['token']}").status_code == 200


        # Make sure that the secret link for the record was created
        record = service.read(identity=identity, id_=record.id)
        secret_links = record._obj.parent.access.links
        assert len(secret_links) == 1
        secret_link = secret_links[0].resolve()
        assert secret_link.token == args["token"]
        assert secret_link.permission_level == "view"
        assert secret_link.origin == f"request:{request.id}"



def test_with_rdm_service(app, client, users, minimal_record):
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
        assert client.get(f"/records/{record.id}").status_code == 200
        assert client.get(f"/records/{record.id}/files").status_code == 403
        assert (
            client.get(f"/records/{record.id}/files/test.txt/content").status_code
            == 403
        )



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

        assert len(outbox) == 3 # GuestAccessRequestSubmittedNotificationBuilder is not dummy unlike in invenio
        submit_message = outbox[1]
        assert "/me/requests/{}".format(request.id) in submit_message.html

        # Accept the request
        # This is expected to send out another email, containing the new secret link
        current_requests_service.execute_action(identity, request.id, "accept", data={})
        assert len(outbox) == 4
        success_message = outbox[3]
        match = link_regex.search(str(success_message.body))
        assert match
        access_url = match.group(1)
        parsed = urllib.parse.urlparse(access_url)
        args = {k: v for k, v in [kv.split("=") for kv in parsed.query.split("&")]}
        assert "token" in args

        # The user can now access the record and its files via the secret link
        assert client.get(f"/records/{record.id}/files").status_code == 403
        assert client.get(f"/records/{record.id}?token={args['token']}").status_code == 200
        assert client.get(f"/records/{record.id}/files").status_code == 200 # todo is this correct - is it ok that the token is cached somewhere?
        assert client.get(f"/records/{record.id}/files?token={args['token']}").status_code == 200
        assert client.get(f"/records/{record.id}/files/test.txt/content?token={args['token']}").status_code == 200


        # Make sure that the secret link for the record was created
        record = service.read(identity=identity, id_=record.id)
        secret_links = record._obj.parent.access.links
        assert len(secret_links) == 1
        secret_link = secret_links[0].resolve()
        assert secret_link.token == args["token"]
        assert secret_link.permission_level == "view"
        assert secret_link.origin == f"request:{request.id}"



def test_simple_user_access_request_flow(app, client, users, minimal_record):
    """Test a the simple user-based access request flow."""

    with app.extensions["mail"].record_messages() as outbox:
        # Log in a user (whose ID we need later)
        record_owner = users[0].user
        user = users[1].user
        identity = Identity(record_owner.id)
        identity.provides.add(any_user)
        identity.provides.add(authenticated_user)
        identity.provides.add(UserNeed(record_owner.id))
        login_user(user)
        login_user_via_session(client, email=user.email)

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

        # There's no access grants in the record yet
        assert not record._obj.parent.access.grants

        # The user can access the record, but not the files
        assert client.get(f"/modela/{record.id}").status_code == 200
        assert client.get(f"/modela/{record.id}/files").status_code == 403
        assert (
            client.get(f"/modela/{record.id}/files/test.txt/content").status_code
            == 403
        )

        # The user creates an access request
        response = client.post(
            f"/records/{record.id}/access/request",
            json={
                "message": "Please give me access!",
                "email": user.email,
                "full_name": "ABC",
            },
        )
        request_id = response.json["id"]
        assert response.status_code == 200
        assert len(outbox) == 1
        submit_message = outbox[0]
        assert "/me/requests/{}".format(request_id) in submit_message.html

        # The record owner approves the access request
        current_requests_service.execute_action(identity, request_id, "accept", data={})
        assert len(outbox) == 2
        success_message = outbox[1]
        assert record.to_dict()["links"]["self_html"] in success_message.body

        # Now, the user has permission to view the record's files!
        assert client.get(f"/modela/{record.id}").status_code == 200
        assert client.get(f"/modela/{record.id}/files").status_code == 200
        assert (
            client.get(f"/modela/{record.id}/files/test.txt/content").status_code
            == 200
        )

        # Verify the created access grant
        record = service.read(identity=identity, id_=record.id)
        grants = record._record.parent.access.grants
        assert len(grants) == 1
        assert grants[0].to_dict() == {
            "subject": {"type": "user", "id": str(user.id)},
            "permission": "view",
            "origin": f"request:{request_id}",
        }