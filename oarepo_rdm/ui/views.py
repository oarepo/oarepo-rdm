#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""UI blueprints for invenio-app-rdm."""

from __future__ import annotations

from typing import Any, cast

from flask import Blueprint, Flask
from invenio_app_rdm.records_ui.searchapp import search_app_context
from invenio_app_rdm.records_ui.views.filters import (
    can_list_files,
    compact_number,
    custom_fields_search,
    get_scheme_label,
    has_images,
    has_previewable_files,
    localize_number,
    make_files_preview_compatible,
    namespace_url,
    order_entries,
    pid_url,
    select_preview_file,
    to_previewer_files,
    transform_record,
    truncate_number,
)
from invenio_app_rdm.records_ui.views.records import (
    draft_not_found_error,
    not_found_error,
    record_export,
    record_file_download,
    record_file_preview,
    record_from_pid,
    record_media_file_download,
    record_permission_denied_error,
    record_thumbnail,
    record_tombstone_error,
)
from invenio_app_rdm.views import create_url_rule
from invenio_drafts_resources.resources.records.errors import DraftNotCreatedError
from invenio_pidstore.errors import (
    PIDDeletedError,
    PIDDoesNotExistError,
    PIDUnregistered,
)
from invenio_rdm_records.services.errors import RecordDeletedException
from invenio_records_resources.services.errors import (
    FileKeyNotFoundError,
    PermissionDeniedError,
    RecordPermissionDeniedError,
)
from sqlalchemy.orm.exc import NoResultFound


def create_records_blueprint(app: Flask) -> Blueprint:
    """Create the UI blueprint for the RDM records."""
    blueprint = Blueprint("invenio_app_rdm_records", __name__)
    routes: dict[str, Any] = cast("dict[str, Any]", app.config.get("APP_RDM_ROUTES"))

    # Record URL rules not covered by oarepo-ui
    rdm_records_ext = app.extensions["invenio-rdm-records"]
    schemes = rdm_records_ext.records_service.config.pids_providers.keys()
    schemes = ",".join(schemes)
    if schemes:
        blueprint.add_url_rule(
            **create_url_rule(
                routes["record_from_pid"].format(schemes=schemes),
                default_view_func=record_from_pid,
            )
        )

    blueprint.add_url_rule(
        **create_url_rule(
            routes["record_export"],
            default_view_func=record_export,
        )
    )

    blueprint.add_url_rule(
        **create_url_rule(
            routes["record_file_preview"],
            default_view_func=record_file_preview,
        )
    )

    blueprint.add_url_rule(
        **create_url_rule(
            routes["record_file_download"],
            default_view_func=record_file_download,
        )
    )
    blueprint.add_url_rule(
        **create_url_rule(
            routes["record_thumbnail"],
            default_view_func=record_thumbnail,
        )
    )

    blueprint.add_url_rule(
        **create_url_rule(
            routes["record_media_file_download"],
            default_view_func=record_media_file_download,
        )
    )

    # Register error handlers
    blueprint.register_error_handler(PIDDeletedError, record_tombstone_error)
    blueprint.register_error_handler(PIDDoesNotExistError, not_found_error)
    blueprint.register_error_handler(PIDUnregistered, not_found_error)
    blueprint.register_error_handler(KeyError, not_found_error)
    blueprint.register_error_handler(FileKeyNotFoundError, not_found_error)
    blueprint.register_error_handler(NoResultFound, not_found_error)
    blueprint.register_error_handler(DraftNotCreatedError, draft_not_found_error)
    blueprint.register_error_handler(PermissionDeniedError, record_permission_denied_error)
    blueprint.register_error_handler(RecordPermissionDeniedError, record_permission_denied_error)
    blueprint.register_error_handler(RecordDeletedException, record_tombstone_error)

    # Register template filters
    blueprint.add_app_template_filter(can_list_files)
    blueprint.add_app_template_filter(make_files_preview_compatible)
    blueprint.add_app_template_filter(pid_url)
    blueprint.add_app_template_filter(select_preview_file)
    blueprint.add_app_template_filter(to_previewer_files)
    blueprint.add_app_template_filter(has_previewable_files)
    blueprint.add_app_template_filter(order_entries)
    blueprint.add_app_template_filter(get_scheme_label)
    blueprint.add_app_template_filter(has_images)
    blueprint.add_app_template_filter(localize_number)
    blueprint.add_app_template_filter(compact_number)
    blueprint.add_app_template_filter(truncate_number)
    blueprint.add_app_template_filter(namespace_url)
    blueprint.add_app_template_filter(custom_fields_search)
    blueprint.add_app_template_filter(transform_record)

    # Register context processor
    blueprint.app_context_processor(search_app_context)

    return blueprint
