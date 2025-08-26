#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
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
