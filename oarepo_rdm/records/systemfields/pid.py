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
