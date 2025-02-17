from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.resolver import Resolver
from invenio_records.systemfields import (
    ModelField,
    RelatedModelField,
    RelatedModelFieldContext,
)
from invenio_records_resources.records.systemfields.pid import PIDFieldContext, PIDField
from sqlalchemy import inspect
from oarepo_communities.utils import get_service_from_schema_type
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.errors import PIDDoesNotExistError

from oarepo_rdm.proxies import current_oarepo_rdm


class OARepoPIDFieldContext(PIDFieldContext):
    """PIDField context.

    This class implements the class-level methods available on a PIDField. I.e.
    when you access the field through the class, for instance:

    .. code-block:: python

        Record.pid.resolve('...')
        Record.pid.session_merge(record)
    """
    on_draft_record = False

    def resolve(self, pid_value, registered_only=False, with_deleted=False):
        """Resolve identifier."""

        pid_type = current_oarepo_rdm.get_pid_type_from_pid(pid_value)
        record_cls = current_oarepo_rdm.record_cls_from_pid_type(pid_type, is_draft=self.on_draft_record)
        return record_cls.pid.resolve(pid_value, registered_only=registered_only, with_deleted=with_deleted)

class OARepoDraftPIDFieldContext(OARepoPIDFieldContext):
    on_draft_record = True

class OARepoPIDField(PIDField):
    """Persistent identifier system field."""
    """
    def __init__(
        self,
        key="id",
        provider=None,
        pid_type=None,
        object_type="rec",
        resolver_cls=None,
        delete=True,
        create=True,
        context_cls=PIDFieldContext,
    ):

        self._provider = provider
        self._pid_type = provider.pid_type if provider else pid_type
        self._object_type = object_type
        self._resolver_cls = resolver_cls or Resolver
        self._delete = delete
        self._create = create
        super().__init__(
            PersistentIdentifier,
            key=key,
            dump=self.dump_obj,
            load=self.load_obj,
            context_cls=context_cls,
        )
    """

    def create(self, record):
        """Method to create a new persistent identifier for the record."""
        # This uses the fields __get__() data descriptor method below
        service = get_service_from_schema_type(record["$schema"])
        # record =

        pid = getattr(record, self.attr_name)
        if pid is None:
            # Create a PID if the object doesn't already have one.
            pid = self._provider.create(
                object_type=self._object_type,
                object_uuid=record.id,
                record=record,
            ).pid

            # Set using the __set__() method
            setattr(record, self.attr_name, pid)
        return pid

    """
    def delete(self, record):

        pid = getattr(record, self.attr_name)
        if pid is not None:
            if not inspect(pid).persistent:
                pid = db.session.merge(pid)
            self._provider(pid).delete()

    #
    # Life-cycle hooks
    #
    def post_create(self, record):

        if self._provider and self._create:
            self.create(record)

    def post_delete(self, record, force=False):

        if self._delete:
            self.delete(record)

    #
    # Helpers
    #
    @staticmethod
    def load_obj(field, record):

        pid_value = field.get_dictkey(record)
        data = record.get(field.attr_name)

        # If we have both data and pid_value, we construct the object:
        if pid_value and data:
            obj = PersistentIdentifier(
                id=data.get("pk"),
                pid_type=data.get("pid_type"),
                pid_value=pid_value,
                status=data.get("status"),
                object_type=data.get("obj_type"),
                object_uuid=record.id,
            )
            return obj
        return None

    @staticmethod
    def dump_obj(field, record, pid):

        assert isinstance(pid, PersistentIdentifier)

        # Store data values on the attribute name (e.g. 'pid')
        record[field.attr_name] = {
            "pk": pid.id,
            "pid_type": pid.pid_type,
            "status": str(pid.status),
            "obj_type": pid.object_type,
        }

        # Set ID on desired dictionary key.
        field.set_dictkey(record, pid.pid_value)
    """