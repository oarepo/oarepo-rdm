# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""oarepo-rdm UI components."""

from __future__ import annotations

from .communities_memberships_dump import CommunitiesMembershipsComponent
from .deposit_form_defaults import DepositFormDefaultsComponent
from .doi_required import DoiRequiredComponent
from .empty_record_pids import EmptyRecordPidsComponent
from .file_modification import FileModificationComponent
from .files_enabled import FilesEnabledComponent
from .inject_parent_doi import InjectParentDoiComponent
from .pids_config_dump import RDMPIDsConfigComponent
from .rdm_vocabularies_dump import RDMVocabularyOptionsComponent
from .restricted_from_community import RestrictedFromCommunityComponent

__all__ = [
    "CommunitiesMembershipsComponent",
    "DepositFormDefaultsComponent",
    "DoiRequiredComponent",
    "EmptyRecordPidsComponent",
    "FileModificationComponent",
    "FilesEnabledComponent",
    "InjectParentDoiComponent",
    "RDMPIDsConfigComponent",
    "RDMVocabularyOptionsComponent",
    "RestrictedFromCommunityComponent",
]
