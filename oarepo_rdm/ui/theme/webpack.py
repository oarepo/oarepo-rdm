#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
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
