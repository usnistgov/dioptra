#!/bin/bash

shopt -s extglob
set -euo pipefail

{% set services = ["init-copy-nginx-01", "init-copy-nginx-02", "init-copy-db-01", "init-copy-db-02", "init-set-permissions-01", "init-set-permissions-02", "init-set-permissions-03", "init-set-permissions-04", "init-copy-minio-01", "init-copy-minio-02", "init-clone-dioptra-repo-01"] -%}
{% if cookiecutter.nginx_use_https.lower() == "true" and cookiecutter.minio_use_https.lower() == "true" -%}
init_services=({{ services|join(" ") }})
{% elif cookiecutter.nginx_use_https.lower() != "true" and cookiecutter.minio_use_https.lower() == "true" -%}
init_services=({{ services|reject("eq", "init-copy-nginx-02")|join(" ") }})
{% elif cookiecutter.nginx_use_https.lower() == "true" and cookiecutter.minio_use_https.lower() != "true" -%}
init_services=({{ services|reject("eq", "init-copy-minio-01")|reject("eq", "init-copy-minio-02")|join(" ") }})
{% else -%}
init_services=({{ services|reject("eq", "init-copy-nginx-02")|reject("eq", "init-copy-minio-01")|reject("eq", "init-copy-minio-02")|join(" ") }})
{% endif %}
for service in ${init_services[@]}; do
  docker-compose -f docker-compose.init.yml run --rm ${service}
done

{% set minio_new_users = ["MLFLOW_TRACKING", "RESTAPI"] -%}
MINIO_ENDPOINT_ALIAS="minio"
PLUGINS_BUILTINS_DIR="dioptra_builtins"

while IFS="=" read -r key value; do
  case "${key}" in
    {% for new_user in minio_new_users -%}
    "MINIO_{{ new_user }}_USER") MINIO_{{ new_user }}_USER="$value" ;;
    "MINIO_{{ new_user }}_PASSWORD") MINIO_{{ new_user }}_PASSWORD="$value" ;;
    "MINIO_{{ new_user }}_USER_POLICY") MINIO_{{ new_user }}_USER_POLICY="$value" ;;
    {% endfor -%}
    "MINIO_ROOT_USER") MINIO_ROOT_USER="$value" ;;
    "MINIO_ROOT_PASSWORD") MINIO_ROOT_PASSWORD="$value" ;;
  esac
done < "secrets/{{ cookiecutter.container_slug_prefix }}-minio.env"

docker-compose -f docker-compose.init.yml up -d {{ cookiecutter.container_slug_prefix }}-minio {{ cookiecutter.container_slug_prefix }}-db

./wait-for-it.sh localhost:39000 --strict --timeout=300 -- docker-compose -f docker-compose.init.yml run --rm mc -c {{ '"' }}\
  mc alias set ${MINIO_ENDPOINT_ALIAS} {{ "https" if cookiecutter.minio_use_https.lower() == "true" else "http" }}://{{ cookiecutter.container_slug_prefix }}-minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD} && \
  {% for new_user in minio_new_users -%}
  mc admin user add ${MINIO_ENDPOINT_ALIAS} {{ '${MINIO_' ~ new_user ~ '_USER}' }} {{ '${MINIO_' ~ new_user ~ '_PASSWORD}' }} && \
  mc admin policy set ${MINIO_ENDPOINT_ALIAS} {{ '${MINIO_' ~ new_user ~ '_USER_POLICY}' }} user={{ '${MINIO_' ~ new_user ~ 'USER}' }} && \
  {% endfor -%}
  mc mb --p ${MINIO_ENDPOINT_ALIAS}/plugins ${MINIO_ENDPOINT_ALIAS}/workflow ${MINIO_ENDPOINT_ALIAS}/mlflow-tracking && \
  mc mirror --overwrite --remove /init-repos/dioptra/task-plugins/${PLUGINS_BUILTINS_DIR}/ ${MINIO_ENDPOINT_ALIAS}/plugins/${PLUGINS_BUILTINS_DIR}
  {{ '"' }}

./wait-for-it.sh localhost:35432 --strict --timeout=300 -- docker-compose -f docker-compose.init.yml run --rm {{ cookiecutter.container_slug_prefix }}-restapi --upgrade-db
./wait-for-it.sh localhost:35432 --strict --timeout=300 -- docker-compose -f docker-compose.init.yml run --rm {{ cookiecutter.container_slug_prefix }}-mlflow-tracking --upgrade-db

docker-compose -f docker-compose.init.yml down
