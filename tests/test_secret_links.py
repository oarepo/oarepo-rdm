from io import BytesIO

import pytest
from flask_principal import AnonymousIdentity, Identity, UserNeed
from invenio_access.permissions import any_user, authenticated_user
from invenio_rdm_records.secret_links.permissions import LinkNeed
from invenio_records_resources.services.errors import (
    PermissionDeniedError,
    RecordPermissionDeniedError,
)


@pytest.fixture()
def restricted_record(rdm_records_service, workflow_data, identity_simple):
    """Restricted record fixture."""
    service = rdm_records_service

    data = {
        "$schema": "local://modela-1.0.0.json",
        "metadata": {"title": "blah", "cdescription": "bbb"},
        "files": {"enabled": True},
        "access": {"record": "restricted", "files": "restricted"},
        **workflow_data,
    }

    # Create
    draft = service.create(identity_simple, data)

    # Add a file
    service.draft_files.init_files(
        identity_simple, draft.id, data=[{"key": "test.pdf"}]
    )
    service.draft_files.set_file_content(
        identity_simple, draft.id, "test.pdf", BytesIO(b"test file")
    )
    service.draft_files.commit_file(identity_simple, draft.id, "test.pdf")

    # Publish
    record = service.publish(identity_simple, draft.id)

    # Put in edit mode so that draft exists
    draft = service.edit(identity_simple, draft.id)

    return record


@pytest.mark.skip(reason="not used for now")
def test_permission_levels(
    rdm_records_service, restricted_record, identity_simple, search_clear
):
    """Test invalid permission level."""
    service = rdm_records_service

    id_ = restricted_record.id
    view_link = service.access.create_secret_link(
        identity_simple, id_, {"permission": "view"}
    )
    preview_link = service.access.create_secret_link(
        identity_simple, id_, {"permission": "preview"}
    )
    edit_link = service.access.create_secret_link(
        identity_simple, id_, {"permission": "edit"}
    )

    # == Anonymous user
    anon = AnonymousIdentity()
    anon.provides.add(any_user)

    # Deny anonymous to read restricted record and draft
    pytest.raises(RecordPermissionDeniedError, service.read, anon, id_)
    pytest.raises(PermissionDeniedError, service.files.list_files, anon, id_)
    pytest.raises(PermissionDeniedError, service.read_draft, anon, id_)
    with pytest.raises(PermissionDeniedError):
        service.draft_files.list_files(anon, id_)

    # === Anonymous user with view link ===
    anon.provides.add(LinkNeed(view_link.id))

    # Allow anonymous with view link to read record
    service.read(anon, id_)
    service.files.list_files(anon, id_)

    # Deny anonymous with view link to read draft
    pytest.raises(PermissionDeniedError, service.read_draft, anon, id_)
    with pytest.raises(PermissionDeniedError):
        service.draft_files.list_files(anon, id_)

    # === Anonymous user with preview link ===
    anon.provides.remove(LinkNeed(view_link.id))
    anon.provides.add(LinkNeed(preview_link.id))

    # Allow anonymous with preview link to read record and draft
    service.read(anon, id_)
    service.files.list_files(anon, id_)
    service.read_draft(anon, id_)
    service.draft_files.list_files(anon, id_)
    service.draft_files.get_file_content(anon, id_, "test.pdf")
    service.draft_files.read_file_metadata(anon, id_, "test.pdf")

    # Deny anonymous with preview link to update/delete/edit/publish draft
    pytest.raises(PermissionDeniedError, service.update_draft, anon, id_, {})
    pytest.raises(PermissionDeniedError, service.edit, anon, id_)
    pytest.raises(PermissionDeniedError, service.delete_draft, anon, id_)
    pytest.raises(PermissionDeniedError, service.new_version, anon, id_)
    pytest.raises(PermissionDeniedError, service.publish, anon, id_)
    with pytest.raises(PermissionDeniedError):
        service.draft_files.init_files(anon, id_, {})
    with pytest.raises(PermissionDeniedError):
        service.draft_files.update_file_metadata(anon, id_, "test.pdf", {})
    with pytest.raises(PermissionDeniedError):
        service.draft_files.commit_file(anon, id_, "test.pdf")
    with pytest.raises(PermissionDeniedError):
        service.draft_files.delete_file(anon, id_, "test.pdf")
    with pytest.raises(PermissionDeniedError):
        service.draft_files.delete_all_files(anon, id_)
    with pytest.raises(PermissionDeniedError):
        service.draft_files.set_file_content(anon, id_, "test.pdf", None)

    # === Authenticated user with edit link ===
    i = Identity(100)
    i.provides.add(UserNeed(100))
    i.provides.add(authenticated_user)
    i.provides.add(LinkNeed(edit_link.id))

    # Allow user with edit link to read record and draft
    service.read(i, id_)
    service.files.list_files(i, id_)
    service.read_draft(i, id_)
    service.draft_files.list_files(i, id_)
    service.draft_files.get_file_content(i, id_, "test.pdf")
    service.draft_files.read_file_metadata(i, id_, "test.pdf")

    # Deny user with edit link to share the links
    with pytest.raises(PermissionDeniedError):
        service.access.create_secret_link(i, id_, {})
    with pytest.raises(PermissionDeniedError):
        service.access.read_all_secret_links(i, id_)
    with pytest.raises(PermissionDeniedError):
        service.access.read_secret_link(i, id_, edit_link.id)
    with pytest.raises(PermissionDeniedError):
        service.access.update_secret_link(i, id_, edit_link.id, {})
    with pytest.raises(PermissionDeniedError):
        service.access.delete_secret_link(i, id_, edit_link.id)

    # Allow user with edit link to update, delete, edit, publish
    draft = service.read_draft(i, id_)
    data = draft.data
    data["metadata"]["title"] = "allow it"
    service.update_draft(i, id_, data)
    service.delete_draft(i, id_)
    test = service.edit(i, id_)
    service.publish(i, id_)
    new_draft = service.new_version(i, id_)
    new_id = new_draft.id
    service.import_files(i, new_id)
    service.draft_files.delete_file(i, new_id, "test.pdf")
