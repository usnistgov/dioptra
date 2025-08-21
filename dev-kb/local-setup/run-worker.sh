#!/usr/bin/env bash

_dioptra_worker_lib="${DIOPTRA_WORKER_LIB:-tensorflow-cpu}"

# Exit early and print message if uv is not installed
if ! command -v uv >/dev/null 2>&1; then
    echo "uv is not installed, run the following command to install it, then try again:"
    echo ""
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Ensure your environment is up-to-date
cd ${DIOPTRA_CODE}
uv sync --extra worker --extra "${_dioptra_worker_lib}"

source ${DIOPTRA_CODE}/${DIOPTRA_VENV}/bin/activate
cd ${DIOPTRA_DEPLOY}/workdir
dioptra-worker-v1 "Configured-as: $_dioptra_worker_lib"
