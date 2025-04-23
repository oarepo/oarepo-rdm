#!/bin/bash

PYTHON="${PYTHON:-python3}"
export PYTHONWARNINGS=ignore

set -e

OAREPO_VERSION="${OAREPO_VERSION:-12}"

export PIP_EXTRA_INDEX_URL=https://gitlab.cesnet.cz/api/v4/projects/1408/packages/pypi/simple
export UV_EXTRA_INDEX_URL=https://gitlab.cesnet.cz/api/v4/projects/1408/packages/pypi/simple

BUILDER_VENV=".venv-builder"
export INVENIO_INVENIO_RDM_ENABLED=true

if test -d $BUILDER_VENV ; then
	rm -rf $BUILDER_VENV
fi

$PYTHON -m venv $BUILDER_VENV
. $BUILDER_VENV/bin/activate
pip install -U setuptools pip wheel
pip install oarepo-model-builder oarepo-model-builder-drafts oarepo-model-builder-files oarepo-model-builder-drafts-files oarepo-model-builder-rdm

if true ; then
    test -d model-a && rm -rf model-a
    test -d model-b && rm -rf model-b
    test -d model-c && rm -rf model-c
    oarepo-compile-model tests/modela.yaml --output-directory model-a -vvv
    oarepo-compile-model tests/modelb.yaml --output-directory model-b -vvv
    oarepo-compile-model tests/modelc.yaml --output-directory model-c -vvv
fi

if [ -d .venv-tests ] ; then
    rm -rf .venv-tests
fi

$PYTHON -m venv .venv-tests
. .venv-tests/bin/activate

pip install -U setuptools pip wheel
pip install "oarepo[tests,rdm]==${OAREPO_VERSION}.*"
pip install -e model-a
pip install -e model-b
pip install -e model-c

pip install oarepo-workflows
pip install oarepo-requests
pip install oarepo-communities
pip install ".[tests]"

pytest tests
