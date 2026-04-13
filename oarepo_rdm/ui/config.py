#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Configuration class for RDM record UI resources."""

from __future__ import annotations

from oarepo_ui.resources.components import (
    AllowedHtmlTagsComponent,
    BabelComponent,
    CustomFieldsComponent,
    EmptyRecordAccessComponent,
    FilesComponent,
    FilesLockedComponent,
    FilesQuotaAndTransferComponent,
    PermissionsComponent,
    RecordRestrictionComponent,
)
from oarepo_ui.resources.records.config import RecordsUIResourceConfig

from oarepo_rdm.ui.components import (
    CommunitiesMembershipsComponent,
    DepositFormDefaultsComponent,
    DoiRequiredComponent,
    EmptyRecordPidsComponent,
    FilesEnabledComponent,
    InjectParentDoiComponent,
    RDMVocabularyOptionsComponent,
)


class RDMRecordsUIResourceConfig(RecordsUIResourceConfig):
    """Configuration for RDM UI resources.

    This config provides commonly used UI resource components for RDM-based projects.
    Application-specific configs should inherit from this class and can extend
    the components list:

    Example::

        class DatasetsUIResourceConfig(
            RDMRecordsUIResourceConfig
        ):
            url_prefix = "/datasets"
            blueprint_name = "datasets_ui"
            model_name = "datasets"

            components = (
                *RDMRecordsUIResourceConfig.components,
                # Add your custom components here
            )
    """

    components = (
        AllowedHtmlTagsComponent,
        BabelComponent,
        PermissionsComponent,
        FilesComponent,
        FilesEnabledComponent,
        EmptyRecordPidsComponent,
        DepositFormDefaultsComponent,
        CustomFieldsComponent,
        RecordRestrictionComponent,
        EmptyRecordAccessComponent,
        FilesLockedComponent,
        FilesQuotaAndTransferComponent,
        RDMVocabularyOptionsComponent,
        CommunitiesMembershipsComponent,
        InjectParentDoiComponent,
        DoiRequiredComponent,
    )

    # Default components for RDM UI resources.
    #
    # These components handle common functionality like:
    # - AllowedHtmlTagsComponent: Sanitizes HTML tags in record content
    # - BabelComponent: Provides internationalization support
    # - PermissionsComponent: Handles permission checks
    # - FilesComponent: Manages file handling
    # - CustomFieldsComponent: Processes custom fields
    # - RecordRestrictionComponent: Handles access restrictions
    # - EmptyRecordAccessComponent: Sets default access for new records
    # - FilesLockedComponent: Manages file locking state
    # - FilesQuotaAndTransferComponent: Handles file quota and transfer limits
    # - RDMVocabularyOptionsComponent: Provides RDM vocabulary options
    # - CommunitiesMembershipsComponent: Handles community memberships
