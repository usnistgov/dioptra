#!/usr/bin/env bash


source ${DIOPTRA_CODE}/${DIOPTRA_VENV}/bin/activate
cd ${DIOPTRA_DEPLOY}/workdir
dioptra-worker-v1 'Tensorflow CPU'
