#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from .models import modela, modelb, modelc

modela_service = modela.proxies.current_service
modelb_service = modelb.proxies.current_service
modelc_service = modelc.proxies.current_service


def test_list(rdm_records_service, users, logged_client, search_clear):
    user = users[0]
    client = logged_client(user)

    sample_draft = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modela-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    _publish = rdm_records_service.publish(user.identity, sample_draft["id"])

    modela_service.indexer.refresh()
    modela_service.draft_indexer.refresh()

    result = client.get("/api/records")
    assert len(result.json["hits"]["hits"]) == 1


def test_read(rdm_records_service, users, logged_client, search_clear):
    user = users[0]
    client = logged_client(user)

    sample = rdm_records_service.create(
        user.identity,
        data={
            "$schema": "local://modela-v1.0.0.json",
            "files": {"enabled": False},
        },
    )
    _publish = rdm_records_service.publish(user.identity, sample["id"])

    result = client.get(f"/api/records/{sample['id']}")
    assert result.status_code == 200
