#!/usr/bin/env bash

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
if [ -a ${DIOPTRA_VENV} ] ; then
    echo "${DIOPTRA_VENV} directory already exists. Skipping environment creation."
else
    python3 -m venv ${DIOPTRA_VENV}
    source ${DIOPTRA_VENV}/bin/activate
    python3 -m pip install --upgrade pip pip-tools
    pip-sync requirements/${DIOPTRA_PLATFORM}-py3.11-requirements-dev.txt
fi

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