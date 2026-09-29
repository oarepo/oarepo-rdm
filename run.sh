#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT
#
# Wrapper script for oarepo-cli library commands.
# Copy this file as "run.sh" to your library project root.
#
# This script:
# - Sets up a local .tools/venv (using uv) on first run
# - Installs oarepo-cli into that venv
# - Forwards all arguments to "oarepo-cli library <args>"
#
# Usage:
#   ./run.sh venv          # runs: oarepo-cli library venv
#   ./run.sh test          # runs: oarepo-cli library test
#   ./run.sh self-update   # removes .tools/venv and reinstalls oarepo-cli
#

set -euo pipefail

base_dir="$(dirname "$0")"

if [ ! -f "${base_dir}/.runner.sh" ]; then
  echo "Downloading .runner.sh from oarepo repository..." >&2
  curl -o "${base_dir}/.runner.sh" https://raw.githubusercontent.com/oarepo/oarepo/main/tools/library_runner.sh
  chmod +x "${base_dir}/.runner.sh"
fi

"${base_dir}/.runner.sh" "$@"