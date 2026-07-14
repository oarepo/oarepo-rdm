#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Records service backing the community collections service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask import current_app
from invenio_rdm_records.proxies import current_rdm_records_service

from .service import OARepoCommunityRecordsService

if TYPE_CHECKING:
    from invenio_access.permissions import Identity
    from invenio_records_resources.services.records.results import RecordList


class OARepoCollectionsRecordsService(OARepoCommunityRecordsService):
    """Community records service used by collections.

    Behaves like the community-scoped multiplexed search, except for the
    designated global-collections community (``INVENIO_COLLECTIONS_COMMUNITY_SLUG``),
    whose collections search across every record instead of only records tagged
    with the holder community.
    """

    @override
    def search(
        self,
        identity: Identity,
        community_id: str,
        params: dict[str, Any] | None = None,
        search_preference: str | None = None,
        extra_filter: Any | None = None,
        scan: bool = False,
        scan_params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> RecordList:
        """Search a community's records, unscoped for the global-collections community."""
        slug = current_app.config.get("INVENIO_COLLECTIONS_COMMUNITY_SLUG")
        if slug is not None:
            community = self.community_cls.pid.resolve(community_id)
            if community.slug == slug:
                # Global collection tree: search all records, not community-scoped.
                return current_rdm_records_service.search(
                    identity,
                    params=params or {},
                    search_preference=search_preference,
                    extra_filter=extra_filter,
                    **kwargs,
                )
        # Community-scoped fallback: only exercised for a real community member,
        # for which we dont have fixtures necessary (they live in oarepo-communities etc. and
        # we dont want to add those dependencies here)
        return super().search(  # pragma: no cover
            identity,
            community_id,
            params,
            search_preference,
            extra_filter,
            scan,
            scan_params,
            **kwargs,
        )
