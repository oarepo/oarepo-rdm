# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Sitemap content for OARepo record models.

InvenioRDM's own `SitemapSectionOfRDMRecords` reads the single RDM records
index and links to the stock `invenio_app_rdm_records.record_detail` page.
An OARepo repository has neither: each model has its own index and its own
record detail page, so the sitemap would stay empty.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, override

from invenio_search.api import RecordsSearchV2
from invenio_sitemap import SitemapSection, format_to_w3c
from oarepo_runtime import current_runtime

if TYPE_CHECKING:
    from collections.abc import Iterator

log = logging.getLogger(__name__)


class SitemapSectionOfOARepoRecords(SitemapSection):
    """Sitemap entries for the published, public records of all RDM-like models.

    Only models that have a UI (a record detail page) are listed. Restricted
    and deleted records are left out, same as in InvenioRDM.
    """

    @override
    def iter_entities(self) -> Iterator[dict[str, Any]]:
        """Iterate over public published records of every model."""
        for model in current_runtime.rdm_models:
            if model.ui_blueprint_name is None or model.record_cls is None:
                continue
            try:
                index_name = model.record_cls.index._name  # noqa: SLF001  # ty: ignore[missing-attribute]
                records_scan = (
                    RecordsSearchV2(index=index_name)
                    .filter("term", **{"access.record": "public"})
                    .filter("term", deletion_status="P")
                    .sort("-updated")
                    .params(preserve_order=True)
                    .source(["id", "updated"])
                    .scan()
                )
                for record in records_scan:
                    loc = model.ui_url("record_detail", pid_value=record["id"])
                    if loc is not None:
                        yield {"loc": loc, "updated": record["updated"]}
            except Exception:
                # one broken model must not take the other models (and the
                # other sections) out of the sitemap
                log.exception("Could not generate sitemap entries for model %s", model.code)

    @override
    def to_dict(self, entity: dict[str, Any]) -> dict[str, Any]:
        """Convert a record entity to a sitemap entry."""
        return {
            "loc": entity["loc"],
            "lastmod": format_to_w3c(entity["updated"]),
        }
