#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""oarepo-rdm UI components."""

from __future__ import annotations

from .communities_memberships_dump import CommunitiesMembershipsComponent
from .deposit_form_defaults import DepositFormDefaultsComponent
from .doi_required import DoiRequiredComponent
from .empty_record_pids import EmptyRecordPidsComponent
from .files_enabled import FilesEnabledComponent
from .inject_parent_doi import InjectParentDoiComponent
from .rdm_vocabularies_dump import RDMVocabularyOptionsComponent

__all__ = [
    "CommunitiesMembershipsComponent",
    "DepositFormDefaultsComponent",
    "DoiRequiredComponent",
    "EmptyRecordPidsComponent",
    "FilesEnabledComponent",
    "InjectParentDoiComponent",
    "RDMVocabularyOptionsComponent",
]
