#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Configuration of the RDM service."""

from __future__ import annotations

from invenio_rdm_records.services.config import RDMRecordServiceConfig


class OARepoRDMServiceConfig(RDMRecordServiceConfig):
    """OARepo extension to RDM record service configuration."""
