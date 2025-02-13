#!/opt/homebrew/bin/bash


cd ${DIOPTRA_CODE}

source ${DIOPTRA_VENV}/bin/activate
dioptra-db autoupgrade
exec flask run