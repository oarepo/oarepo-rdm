from typing import cast

import click
from flask.cli import with_appcontext
from invenio_access.permissions import system_identity
from invenio_accounts.models import User
from invenio_db import db
from invenio_db.uow import UnitOfWork
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_rdm_records.cli import rdm_records
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.records.api import RDMDraft, RDMParent, RDMRecord
from invenio_rdm_records.services import RDMRecordService
from oarepo_runtime.proxies import current_runtime
from sqlalchemy import func


def get_record(record_id: str) -> tuple[RDMRecord | RDMDraft, RDMRecordService]:
    """Get the record from its persistent identifier - might be published or draft."""
    record: RDMRecord | RDMDraft
    try:
        record = current_rdm_records_service.read(system_identity, record_id)._record
    except Exception:
        record = current_rdm_records_service.read_draft(
            system_identity, record_id
        )._record

    specialized_service = cast(
        "RDMRecordService", current_runtime.get_record_service_for_record(record)
    )

    return record, specialized_service


@rdm_records.command("replace-owner")
@click.argument("record-id")
@click.argument("owner-email")
@with_appcontext
def replace_owner(record_id, owner_email):
    """Set the owner of a record. The previous owner will be replaced with the new one."""
    with UnitOfWork() as uow:
        # get the new owner
        owner = db.session.query(User).filter_by(email=owner_email).one()
        record, specialized_service = get_record(record_id)

        click.secho()
        click.secho(
            "Warning: you are about to replace the owner of the record. Are you sure?",
            fg="red",
        )
        click.secho(f"Record id      : {record_id}", fg="yellow")
        click.secho(f"Previous owner : {record.parent.access.owner}", fg="yellow")
        click.secho(f"New owner      : {owner}", fg="yellow")
        click.secho()
        if not click.confirm("Are you sure you want to replace the owner?"):
            return

        # update the owner inside the parent record (will update the owner in all versions of the record)
        parent: RDMParent = record.parent
        parent.access.owner = owner

        # commit the changes
        uow.register(
            ParentRecordCommitOp(
                parent, indexer_context={"service": specialized_service}
            )
        )
        uow.commit()


@rdm_records.command("merge-records")
@click.argument("old-record-id")
@click.argument("new-record-id")
@click.option(
    "--rebase-on-old/--rebase-on-new",
    "direction",
    default=True,
    help="If --rebase-on-old, the versions from the new record will be moved to the top of the old record",
)
@with_appcontext
def merge_records(old_record_id, new_record_id, direction):
    """Merge two RDM records by rebasing one onto the other."""
    rebase_direction = "old" if direction else "new"

    old_record, old_specialized_service = get_record(old_record_id)
    new_record, new_specialized_service = get_record(new_record_id)
    record_count = 0

    with db.session.begin_nested():
        if old_specialized_service is not new_specialized_service:
            click.secho(
                "Error: the records are not from the same service, aborting.", fg="red"
            )
            raise click.Abort()

        old_parent = old_record.parent
        new_parent = new_record.parent

        model_class = old_specialized_service.config.record_cls.model_cls
        draft_class = old_specialized_service.config.draft_cls.model_cls

        if rebase_direction == "old":
            # rebasing on old version -> all versions from the new_parent are moved to the old_parent, new_parent is deleted
            destination_parent = old_parent
            destination_parent_id = old_parent.id
            source_parent = new_parent
            source_parent_id = new_parent.id
        else:
            # rebasing on new version -> all versions from the old_parent are moved to the new_parent, old_parent is deleted
            destination_parent = new_parent
            destination_parent_id = new_parent.id
            source_parent = old_parent
            source_parent_id = old_parent.id

        records_to_move = db.session.query(model_class).filter_by(
            parent_id=source_parent_id
        )
        drafts_to_move = db.session.query(draft_class).filter_by(
            parent_id=source_parent_id
        )

        destination_last_index = (
            db.session.query(func.max(model_class.index))
            .filter_by(parent_id=destination_parent_id)
            .scalar()
            or 0
        )

        record_count = records_to_move.count()

        # print user the records that will be moved
        click.echo(
            f"Moving records from parent {source_parent_id} to parent {destination_parent_id}"
        )
        for record in records_to_move.all():
            click.echo(
                f"  - pid={(record.json or {}).get('id')} uuid={record.id} index={record.index}"
            )
        click.echo("")
        click.echo(
            f"Moving drafts from parent {source_parent_id} to parent {destination_parent_id}"
        )
        for record in drafts_to_move.all():
            click.echo(
                f"  - pid={(record.json or {}).get('id')} uuid={record.id} index={record.index}"
            )
        click.echo("")
        for version_obj in db.session.query(old_record.versions_model_cls).filter_by(
            parent_id=source_parent_id
        ):
            click.echo(
                f"  -version: latest_id={version_obj.latest_id} latest_index={version_obj.latest_index}"
            )

        click.confirm("Are you sure you want to continue?", abort=True)

        # do a bulk update of the parent_id for all records
        records_to_move.update(
            {
                "parent_id": destination_parent_id,
                "index": model_class.index + destination_last_index,
            }
        )
        drafts_to_move.update(
            {
                "parent_id": destination_parent_id,
                "index": model_class.index + destination_last_index,
            }
        )

        # latest_id is max of ids
        latest_index = (
            db.session.query(func.max(model_class.index))
            .filter(model_class.parent_id == destination_parent_id)
            .scalar()
        )
        latest_id = (
            db.session.query(model_class.id)
            .filter(
                model_class.parent_id == destination_parent_id,
                model_class.index == latest_index,
            )
            .scalar()
        )

        # update versions_model_cls
        versions_objects = db.session.query(old_record.versions_model_cls).filter_by(
            parent_id=destination_parent_id
        )
        versions_objects.update({"latest_id": latest_id, "latest_index": latest_index})

        click.secho("After the move, we will have the following published records:")
        # for each of the records, print the id and index
        for record in (
            db.session.query(model_class)
            .filter_by(parent_id=destination_parent_id)
            .order_by("index")
        ):
            click.echo(
                f"  - {(record.json or {}).get('id')} {record.id} {record.index}"
            )
        click.echo("After the move, we will have the following drafts:")
        # and for drafts
        for draft in (
            db.session.query(draft_class)
            .filter_by(parent_id=destination_parent_id)
            .order_by("index")
        ):
            click.echo(f"  - {(draft.json or {}).get('id')} {draft.id} {draft.index}")
            click.echo("")
        for version_obj in db.session.query(old_record.versions_model_cls).filter_by(
            parent_id=destination_parent_id
        ):
            click.echo(
                f"  -version: latest_id={version_obj.latest_id} latest_index={version_obj.latest_index}"
            )
        click.echo("")

        # remove the old parent if it no longer has any records
        db.session.delete(source_parent.model)

        click.confirm("About to commit, are you sure you want to continue?", abort=True)

        db.session.commit()

    # reindex the parent - this will reindex all records with the new parent
    with UnitOfWork() as uow:
        uow.register(ParentRecordCommitOp(destination_parent))
        uow.commit()

    click.secho(
        f"Moved {record_count} records from parent {source_parent_id} to parent {destination_parent_id}",
        fg="green",
    )
    click.secho(
        "Please go to the Datacite Fabrica and remove the old parent from it, this was not done automatically !!!",
        fg="red",
    )
