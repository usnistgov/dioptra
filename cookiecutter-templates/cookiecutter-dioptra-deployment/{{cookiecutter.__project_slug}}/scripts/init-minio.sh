#!/usr/bin/env bash
# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode

shopt -s extglob
set -euo pipefail

BASEDIR="${1}"
MINIO_ENDPOINT_ALIAS="minio"

{% set minio_account_names = ["MLFLOW_TRACKING", "RESTAPI", "WORKER"] -%}
while IFS="=" read -r key value; do
  case "${key}" in
    {% for minio_account_name in minio_account_names -%}
    "MINIO_{{ minio_account_name }}_USER") MINIO_{{ minio_account_name }}_USER="$value" ;;
    "MINIO_{{ minio_account_name }}_PASSWORD") MINIO_{{ minio_account_name }}_PASSWORD="$value" ;;
    "MINIO_{{ minio_account_name }}_POLICIES") MINIO_{{ minio_account_name }}_POLICIES="$value" ;;
    {% endfor -%}
    "MINIO_ROOT_USER") MINIO_ROOT_USER="$value" ;;
    "MINIO_ROOT_PASSWORD") MINIO_ROOT_PASSWORD="$value" ;;
  esac
done < "${BASEDIR}/secrets/{{ cookiecutter.__project_slug }}-minio-accounts.env"

{{ cookiecutter.docker_compose_path }} -f ${BASEDIR}/docker-compose.init.yml up -d minio

{% set minio_policy_names = [
  "builtin-plugins-readonly",
  "builtin-plugins-readwrite",
  "custom-plugins-readonly",
  "custom-plugins-readwrite",
  "dioptra-readonly",
  "mlflow-tracking-readwrite",
  "plugins-readonly",
  "workflow-downloadonly",
  "workflow-uploadonly",
] -%}
{{ cookiecutter.docker_compose_path }} -f ${BASEDIR}/docker-compose.init.yml run --rm mc -c "\
  mc alias set ${MINIO_ENDPOINT_ALIAS} http://{{ cookiecutter.__project_slug }}-minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD} && \
  mc mb --p ${MINIO_ENDPOINT_ALIAS}/plugins ${MINIO_ENDPOINT_ALIAS}/workflow ${MINIO_ENDPOINT_ALIAS}/mlflow-tracking && \
  {% for policy_name in minio_policy_names -%}
  mc admin policy add ${MINIO_ENDPOINT_ALIAS} {{ policy_name }} /s3-policy/{{ policy_name }}-policy.json && \
  {% endfor -%}
  {% for minio_account_name in minio_account_names -%}
  mc admin user add ${MINIO_ENDPOINT_ALIAS} {{ '${MINIO_' ~ minio_account_name ~ '_USER}' }} {{ '${MINIO_' ~ minio_account_name ~ '_PASSWORD}' }} && \
  mc admin policy set ${MINIO_ENDPOINT_ALIAS} {{ '${MINIO_' ~ minio_account_name ~ '_POLICIES}' }} user={{ '${MINIO_' ~ minio_account_name ~ '_USER}' }} && \
  {% endfor -%}
  mc mirror --overwrite --remove /init-repos/dioptra/task-plugins/dioptra_builtins ${MINIO_ENDPOINT_ALIAS}/plugins/dioptra_builtins"

{{ cookiecutter.docker_compose_path }} -f ${BASEDIR}/docker-compose.init.yml down
