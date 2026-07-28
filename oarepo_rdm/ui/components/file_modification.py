#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Component that exposes published-file modification eligibility to the deposit form."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING, Any, cast, override

from invenio_app_rdm.records_ui.utils import evaluate_file_modification
from oarepo_runtime.typing import record_from_result
from oarepo_ui.resources.components import UIResourceComponent

if TYPE_CHECKING:
    from invenio_rdm_records.records.api import RDMDraft
    from oarepo_ui.resources.records.resource import RecordsUIResource


class FileModificationComponent(UIResourceComponent):
    """Expose the file-modification (grace period) evaluation to the deposit form.

    Mirrors invenio-app-rdm: for the edit draft of a published record, evaluate
    whether the current identity may unlock and modify the published files and
    expose the result through the ``deposits-file-modification`` hidden input so
    the file uploader can render the unlock UI.

    The value is kept as its own top-level template variable / hidden input --
    rather than a key inside ``forms_config`` -- to match upstream RDM, which
    passes ``fileModification`` as a dedicated prop and does not expect it inside
    the form config. Keeping it separate avoids polluting a dict whose shape
    upstream owns.

    The grace period is measured from the *published* record's creation date, so
    the published record is read explicitly rather than using the draft (whose
    ``created`` would reset the window on every edit).
    """

    @override
    def before_ui_edit(
        self,
        *,
        render_kwargs: dict,
        identity: Any = None,
        api_record: Any = None,
        **kwargs: Any,
    ) -> None:
        """Expose ``file_modification`` to the edit page for published records.

        :param render_kwargs: template render arguments to mutate in-place; the
            ``file_modification`` key is rendered into the
            ``deposits-file-modification`` hidden input by ``form.html``.
        :param identity: current user identity.
        :param api_record: the draft being edited.
        """
        render_kwargs["file_modification"] = self._evaluate(api_record, identity)

    def _evaluate(self, api_record: Any, identity: Any) -> dict:
        """Evaluate file-modification eligibility for the draft's published record.

        Returns an empty dict when it does not apply (e.g. an unpublished draft),
        mirroring invenio-app-rdm.
        """
        if api_record is None:
            return {}
        record = cast("RDMDraft", record_from_result(api_record))
        if record is None or not record.is_published:
            return {}
        resource = cast("RecordsUIResource", self.resource)
        published = resource.api_service.read(identity, id_=api_record["id"])
        result: dict = evaluate_file_modification(record_from_result(published), identity)
        # ``evaluate_file_modification`` nests a ``PolicyEvaluator.Result`` dataclass
        # under "fileModification"; the template's ``| tojson`` cannot serialize a
        # dataclass, so flatten it to a plain dict for the frontend to read.
        nested = result.get("fileModification")
        if is_dataclass(nested) and not isinstance(nested, type):
            result["fileModification"] = asdict(nested)
        return result
