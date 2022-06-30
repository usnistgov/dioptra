#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-EOSQL
  CREATE USER dioptra;
  CREATE DATABASE restapi;
  CREATE DATABASE mlflow-tracking;
  GRANT ALL PRIVILEGES ON DATABASE restapi TO dioptra;
  GRANT ALL PRIVILEGES ON DATABASE mlflow-tracking TO dioptra;
  ALTER ROLE dioptra ENCRYPTED PASSWORD '${POSTGRES_USER_DIOPTRA_PASSWORD}';
EOSQL
