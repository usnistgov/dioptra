#!/usr/bin/env bash

echo "Your current BASH_VERSION is $BASH_VERSION"
echo "which bash command points to $(which bash)"

cd ${DIOPTRA_CODE}

source ${DIOPTRA_VENV}/bin/activate
dioptra-db autoupgrade
exec flask run