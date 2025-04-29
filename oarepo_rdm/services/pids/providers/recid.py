from invenio_pidstore.models import PIDStatus
from invenio_rdm_records.services.pids.providers.base import PIDProvider
from invenio_pidstore.providers.base import BaseProvider

class VirtualCollectiveRecordPIDProvider(PIDProvider):
    pid_type = "vcrid"
    default_status_with_obj = PIDStatus.NEW

    def generate_id(self, record, **kwargs):
        """Generates an identifier value."""
        return record["id"]

    @classmethod
    def is_enabled(cls, app):
        """Determine if datacite is enabled or not."""
        return True

    @classmethod
    def create(cls, object_type=None, object_uuid=None, options=None, **kwargs):
        assert "record" in kwargs
        return BaseProvider.create(pid_value=kwargs["record"]["id"], object_type=object_type,
                                   object_uuid=object_uuid, options=options, pid_type=cls.pid_type, **kwargs)