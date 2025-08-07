#!/usr/bin/env bash

_dioptra_worker_lib="${DIOPTRA_WORKER_LIB:-tensorflow-cpu}"

# Exit early and print message if uv is not installed
if ! command -v uv >/dev/null 2>&1; then
    echo "uv is not installed, run the following command to install it, then try again:"
    echo ""
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Get Dioptra code from Github
if [ -a ${DIOPTRA_CODE} ] ; then
    echo "Directory ${DIOPTRA_CODE} already exists"
    echo "Skipping git clone"
else
    echo running git clone
    git clone https://github.com/usnistgov/dioptra.git ${DIOPTRA_CODE}
fi

# Checkout the $DIOPTRA_BRANCH branch
echo Checking out $DIOPTRA_BRANCH branch
cd ${DIOPTRA_CODE}
git checkout ${DIOPTRA_BRANCH}
# create working directory to hold database and other files
mkdir -p ${DIOPTRA_DEPLOY}

# set-up python environment
uv sync --extra worker --extra "${_dioptra_worker_lib}"

# Set-up frontend files
if [ -a src/frontend/node_modules ] ; then
    echo "src/frontend/node_modules already exists. Skipping npm install."
else
    echo "Setting Up Frontend with npm install -- this could potentially take a long time (> 10 minutes)"
    cd src/frontend
    npm install
fi

# create working directory for Worker
echo Creating Working directories in ${DIOPTRA_DEPLOY}
mkdir -p ${DIOPTRA_DEPLOY}/workdir/
mkdir -p ${DIOPTRA_DEPLOY}/instance/
