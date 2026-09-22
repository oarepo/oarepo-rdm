# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Proxies for the RDM extension."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import current_app
from werkzeug.local import LocalProxy

if TYPE_CHECKING:
    from oarepo_rdm.ext import OARepoRDM

    current_oarepo_rdm: OARepoRDM


current_oarepo_rdm = LocalProxy(lambda: current_app.extensions["oarepo-rdm"])
