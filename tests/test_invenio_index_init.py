# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from click.testing import CliRunner
from invenio_search.cli import destroy
from oarepo_runtime.cli.search import init


def test_index_init(app):
    runner = CliRunner()

    result = runner.invoke(destroy, ["--yes-i-know", "--force"])
    assert result.exit_code == 0

    result = runner.invoke(init)
    assert result.exit_code == 0
