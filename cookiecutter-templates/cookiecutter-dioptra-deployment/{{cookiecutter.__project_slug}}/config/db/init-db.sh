#!/usr/bin/env bash
set -e

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-EOSQL
	CREATE USER "dioptra";
	CREATE DATABASE "restapi";
	CREATE DATABASE "mlflow-tracking";
	REVOKE ALL ON DATABASE "restapi" FROM "public";
	REVOKE ALL ON DATABASE "mlflow-tracking" FROM "public";
	GRANT ALL PRIVILEGES ON DATABASE "restapi" TO "dioptra";
	GRANT ALL PRIVILEGES ON DATABASE "mlflow-tracking" TO "dioptra";
	ALTER ROLE "dioptra" ENCRYPTED PASSWORD '${POSTGRES_USER_DIOPTRA_PASSWORD}';
EOSQL

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "restapi" <<-EOSQL
	REVOKE USAGE ON SCHEMA "public" FROM "public";
	REVOKE CREATE ON SCHEMA "public" FROM "public";
	GRANT USAGE ON SCHEMA "public" TO "dioptra";
	GRANT CREATE ON SCHEMA "public" TO "dioptra";
EOSQL

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "mlflow-tracking" <<-EOSQL
	REVOKE USAGE ON SCHEMA "public" FROM "public";
	REVOKE CREATE ON SCHEMA "public" FROM "public";
	GRANT USAGE ON SCHEMA "public" TO "dioptra";
	GRANT CREATE ON SCHEMA "public" TO "dioptra";
EOSQL
