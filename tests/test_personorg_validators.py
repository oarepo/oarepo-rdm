#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for person/org identifier validators."""

from __future__ import annotations

import pytest

from oarepo_rdm.initial_config import is_researcher_id, is_scopus_id, is_vedidk


@pytest.mark.parametrize(
    "identifier",
    [
        "A-1234-5678",
        "ABC-0000-9999",
        "abc-1234-5678",
        "AbCdE-2021-0001",
    ],
)
def test_is_researcher_id_valid(identifier: str) -> None:
    assert is_researcher_id(identifier) is True


@pytest.mark.parametrize(
    "identifier",
    [
        "",
        "1234-5678-9012",
        "A-123-5678",
        "A-1234-567",
        "A-1234-56789",
        "A-12a4-5678",
        "A_1234_5678",
        "A-1234-5678 ",
        " A-1234-5678",
        "A--1234-5678",
        "-1234-5678",
    ],
)
def test_is_researcher_id_invalid(identifier: str) -> None:
    assert is_researcher_id(identifier) is False


@pytest.mark.parametrize(
    "identifier",
    [
        "1234567",
        "0000000",
        "  1234567  ",
        "\t1234567\n",
    ],
)
def test_is_vedidk_valid(identifier: str) -> None:
    assert is_vedidk(identifier) is True


@pytest.mark.parametrize(
    "identifier",
    [
        "",
        "123456",
        "12345678",
        "123 4567",
        "abcdefg",
        "1234567a",
        "-1234567",
        "+1234567",
    ],
)
def test_is_vedidk_invalid(identifier: str) -> None:
    assert is_vedidk(identifier) is False


@pytest.mark.parametrize(
    "identifier",
    [
        "123456789",
        "0",
        "12345678.0",
        "7005615766",
    ],
)
def test_is_scopus_id_valid(identifier: str) -> None:
    assert is_scopus_id(identifier) is True


@pytest.mark.parametrize(
    "identifier",
    [
        "",
        "123abc",
        "12 34",
        "12.34",
        "12345.00",
        "-12345",
    ],
)
def test_is_scopus_id_invalid(identifier: str) -> None:
    assert is_scopus_id(identifier) is False
