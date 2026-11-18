#!/bin/sh
# Create the test environment (once) and run the whole test suite.
#
#   scripts/test.sh              every test
#   scripts/test.sh -k reader    arguments are passed to pytest
#
# Needs Python 3.14 (the version the pinned Home Assistant runs on). PYTHON=/path/to/python3.14 selects it,
# VENV=/some/dir puts the environment elsewhere than .venv.
set -eu
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3.14}"
VENV="${VENV:-.venv}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python 3.14 not found (looked for '$PYTHON'); set PYTHON=/path/to/python3.14" >&2
  exit 2
fi
if [ ! -x "$VENV/bin/python" ] || ! cmp -s requirements_test.txt "$VENV/requirements_test.txt"; then
  "$PYTHON" -m venv "$VENV"
  "$VENV/bin/python" -m pip install --quiet --upgrade pip
  "$VENV/bin/python" -m pip install --quiet -r requirements_test.txt
  cp requirements_test.txt "$VENV/requirements_test.txt"
fi
exec "$VENV/bin/python" -m pytest "$@"
