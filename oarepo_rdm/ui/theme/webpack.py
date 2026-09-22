# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Webpack theme definition."""

from __future__ import annotations  # pragma: no cover

from invenio_assets.webpack import WebpackThemeBundle  # pragma: no cover

theme = WebpackThemeBundle(  # pragma: no cover
    __name__,
    "assets",
    default="semantic-ui",
    themes={
        "semantic-ui": {
            "entry": {},
            "dependencies": {},
            "devDependencies": {},
            "aliases": {
                "@js/oarepo_rdm": "js/oarepo_rdm_ui",
            },
        }
    },
)
