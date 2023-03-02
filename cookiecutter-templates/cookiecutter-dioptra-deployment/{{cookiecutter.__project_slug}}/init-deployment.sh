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
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

SCRIPT_CMDNAME="${0##*/}"
SCRIPT_DIRPATH="$(realpath ${0%%/*})"
LOGNAME="Init Deployment"

DOCKER_COMPOSE_INIT_YML="${SCRIPT_DIRPATH}/docker-compose.init.yml"

CONTAINER_DB_PORT="5432"
CONTAINER_SSL_DIR="/ssl"

INIT_ARGBASH_SERVICE="argbash"
INIT_DB_SERVICE="db"
INIT_MLFLOW_TRACKING_SSL_SERVICE="mlflow-tracking-ssl"
INIT_NAMED_VOLUMES_SERVICE="named-volumes"
INIT_NGINX_SSL_SERVICE="nginx-ssl"
INIT_PYTORCHCPU_SSL_SERVICE="pytorchcpu-ssl"
INIT_RESTAPI_SERVICE="restapi"
INIT_RESTAPI_SSL_SERVICE="restapi-ssl"
INIT_TFCPU_SSL_SERVICE="tfcpu-ssl"

DEFAULT_ARG_ENABLE_NGINX_SSL="off"
DEFAULT_ARG_ENABLE_POSTGRES_SSL="off"
DEFAULT_ARG_PLUGINS_BRANCH="main"
DEFAULT_ARG_WORKER_SSL_SERVICE="tfcpu"

_arg_enable_nginx_ssl="${DEFAULT_ARG_ENABLE_NGINX_SSL}"
_arg_enable_postgres_ssl="${DEFAULT_ARG_ENABLE_POSTGRES_SSL}"
_arg_plugins_branch="${DEFAULT_ARG_PLUGINS_BRANCH}"
_arg_worker_ssl_service="${DEFAULT_ARG_WORKER_SSL_SERVICE}"

###########################################################################################
# Print the script help message
#
# Globals:
#   DEFAULT_ARG_PLUGINS_BRANCH
#   DEFAULT_ARG_WORKER_SSL_SERVICE
#   SCRIPT_CMDNAME
# Arguments:
#   Error messages to log, a string
# Returns:
#   None
###########################################################################################

print_help() {
  cat <<-HELPMESSAGE
		Utility that prepares the deployment initialization scripts.

		Usage: init-deployment.sh [--enable-nginx-ssl] [--enable-postgres-ssl]
		                          [--plugins-branch <arg>]
		                          [--worker-ssl-service [tfcpu|pytorchcpu]] [-h|--help]
		        --enable-nginx-ssl: Enable the SSL-enabled configuration settings for nginx image
		        --enable-postgres-ssl: Enable the SSL-enabled configuration settings for postgres
		                               image
		        --plugins-branch: The Dioptra GitHub branch to use when syncing the built-in task
		                          plugins (default: '${DEFAULT_ARG_PLUGINS_BRANCH}')
		        --worker-ssl-service: Image to use when bootstrapping the SSL named volumes for
		                              the worker containers, must be 'tfcpu' or 'pytorchcpu'
		                              (default: '${DEFAULT_ARG_WORKER_SSL_SERVICE}')
		        -h, --help: Prints help
	HELPMESSAGE
}

###########################################################################################
# Print an error log message to stderr
#
# Globals:
#   LOGNAME
# Arguments:
#   Error messages to log, one or more strings
# Returns:
#   None
###########################################################################################

log_error() {
  echo "${LOGNAME}: ERROR -" "${@}" 1>&2
}

###########################################################################################
# Print an informational log message to stdout
#
# Globals:
#   LOGNAME
# Arguments:
#   Info messages to log, one or more strings
# Returns:
#   None
###########################################################################################

log_info() {
  echo "${LOGNAME}: INFO -" "${@}"
}

###########################################################################################
# Validate the value passed to the --worker-ssl-service argument
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_worker_ssl_service() {
  local worker_ssl_service="${1}"

  case "${1}" in
    tfcpu | pytorchcpu)
      return 0
      ;;
    *)
      log_error "Unrecognized value ${1} for --worker-ssl-service, must be either" \
        "'tfcpu' or 'pytorchcpu', exiting..."
      exit 1
      ;;
  esac
}

###########################################################################################
# Parse the script arguments
#
# Globals:
#   _arg_enable_nginx_ssl
#   _arg_enable_postgres_ssl
#   _arg_plugins_branch
#   _arg_worker_ssl_service
# Arguments:
#   Script arguments, an array
# Returns:
#   None
###########################################################################################

parse_args() {
  while (({{ '"${#}"' }} > 0)); do
    case "${1}" in
      -h | --help)
        print_help
        exit 0
        ;;
      --enable-nginx-ssl)
        _arg_enable_nginx_ssl="on"
        shift 1
        ;;
      --enable-postgres-ssl)
        _arg_enable_postgres_ssl="on"
        shift 1
        ;;
      --plugins-branch)
        _arg_plugins_branch="${2}"
        shift 2
        ;;
      --worker-ssl-service)
        validate_worker_ssl_service "${2}"
        _arg_worker_ssl_service="${2}"
        shift 2
        ;;
      *)
        log_error "Unrecognized argument ${1}, exiting..."
        exit 1
        ;;
    esac
  done
}

###########################################################################################
# Wrapper for invoking docker compose
#
# Globals:
#   None
# Arguments:
#   Positional arguments, one or more strings
# Returns:
#   None
###########################################################################################

docker_compose() {
  if ! {{ cookiecutter.docker_compose_path }} "${@}"; then
    log_error "Encountered an error when executing" \
      "{{ cookiecutter.docker_compose_path }}, exiting..."
    exit 1
  fi
}

###########################################################################################
# Wait for services to start
#
# Globals:
#   DOCKER_COMPOSE_INIT_YML
#   INIT_RESTAPI_SERVICE
# Arguments:
#   Name of services, one or more strings
# Returns:
#   None
###########################################################################################

wait_for_services() {
  local services="${@}"
  local wait_for_it_sh="/usr/local/bin/wait-for-it.sh"

  for service in "${services[@]}"; do
    docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" run \
      --rm \
      --entrypoint "${wait_for_it_sh}" \
      "${INIT_RESTAPI_SERVICE}" \
      "${service}" \
      "-t" \
      "0"
  done
}

###########################################################################################
# Add additional certificate authorities to one of the deployment's services
#
# Globals:
#   CONTAINER_SSL_DIR
#   DOCKER_COMPOSE_INIT_YML
# Arguments:
#   Name of the service, a string
# Returns:
#   None
###########################################################################################

add_extra_ca_certificates() {
  local service_name="${1}"
  local args=(
    "/scripts/copy-extra-ca-certificates.sh"
    "--ca-directory"
    "${CONTAINER_SSL_DIR}/ca-certificates"
    "--update"
  )

  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" run \
    --rm \
    "${service_name}" \
    "${args[@]}"
}

###########################################################################################
# Copy a file between the host machine and the services in docker-compose.init.yml
#
# Globals:
#   DOCKER_COMPOSE_INIT_YML
# Arguments:
#   Source path, a string
#   Destination path, a string
# Returns:
#   None
###########################################################################################

docker_compose_init_cp() {
  local src="${1}"
  local dest="${2}"

  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" cp "${src}" "${dest}"
}

###########################################################################################
# Starts a postgres database service as a background process
#
# Globals:
#   DOCKER_COMPOSE_INIT_YML
#   INIT_DB_SERVICE
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_db_service() {
  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" up -d "${INIT_DB_SERVICE}"
}

###########################################################################################
# Enable/disable SSL for the Postgres database
#
# Globals:
#   CONTAINER_DB_PORT
#   INIT_DB_SERVICE
#   DOCKER_COMPOSE_INIT_YML
#   INIT_ARGBASH_SERVICE
#   _arg_enable_postgres_ssl
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

manage_postgres_ssl() {
  local args=()
  local manage_postgres_ssl_file="manage-postgres-ssl.sh"

  if [[ "${_arg_enable_postgres_ssl}" == "on" ]]; then
    args+=(
      "--set-ssl-filepaths"
      "--ssl"
    )
  else
    args+=("--no-ssl")
  fi

  wait_for_services "${INIT_DB_SERVICE}:${CONTAINER_DB_PORT}"

  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" exec \
    "${INIT_DB_SERVICE}" \
    "/bin/bash" \
    "/scripts/${manage_postgres_ssl_file}" \
    "${args[@]}"
}

###########################################################################################
# Runs the database migration for the restapi service
#
# Globals:
#   CONTAINER_DB_PORT
#   DOCKER_COMPOSE_INIT_YML
#   INIT_DB_SERVICE
#   INIT_RESTAPI_SERVICE
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

migrate_restapi_db() {
  local args=(
    "--wait-for"
    "${INIT_DB_SERVICE}:${CONTAINER_DB_PORT}"
    "--upgrade-db"
  )

  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" run \
    --rm \
    "${INIT_RESTAPI_SERVICE}" \
    "${args[@]}"
}

###########################################################################################
# Stops and removes all running containers for services defined in docker-compose.yml
#
# Globals:
#   DOCKER_COMPOSE_INIT_YML
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

stop_services() {
  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" down
}

###########################################################################################
# Prepare the deployment initialization scripts
#
# Globals:
#   DOCKER_COMPOSE_INIT_YML
#   INIT_ARGBASH_SERVICE
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

init_scripts() {
  local args=(
    "/scripts-src/init-scripts.sh"
    "--output"
    "/scripts"
    "/scripts-src/copy-extra-ca-certificates.m4"
    "/scripts-src/file-copy.m4"
    "/scripts-src/git-clone.m4"
    "/scripts-src/globbed-copy.m4"
    "/scripts-src/init-minio.sh"
    "/scripts-src/init-named-volumes.m4"
    "/scripts-src/manage-postgres-ssl.m4"
    "/scripts-src/set-permissions.m4"
  )

  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" run \
    --rm \
    "${INIT_ARGBASH_SERVICE}" \
    "${args[@]}"
}

###########################################################################################
# Copy additional certificate authorities into the deployment's named volumes
#
# Globals:
#   INIT_NGINX_SSL_SERVICE
#   INIT_MLFLOW_TRACKING_SSL_SERVICE
#   INIT_RESTAPI_SSL_SERVICE
#   INIT_TFCPU_SSL_SERVICE
#   INIT_PYTORCHCPU_SSL_SERVICE
#   _arg_worker_ssl_service
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

init_extra_ca_certificates() {
  local services=(
    "${INIT_NGINX_SSL_SERVICE}"
    "${INIT_MLFLOW_TRACKING_SSL_SERVICE}"
    "${INIT_RESTAPI_SSL_SERVICE}"
  )

  if [[ "${_arg_worker_ssl_service}" == "tfcpu" ]]; then
    services+=("${INIT_TFCPU_SSL_SERVICE}")
  elif [[ "${_arg_worker_ssl_service}" == "pytorchcpu" ]]; then
    services+=("${INIT_PYTORCHCPU_SSL_SERVICE}")
  else
    log_error "Unsupported value '${_arg_worker_ssl_service}' passed to" \
      "--worker-ssl-service, exiting..."
    exit 1
  fi

  for service in "${services[@]}"; do
    add_extra_ca_certificates "${service}"
  done
}

###########################################################################################
# Copy config files into the deployment's named volumes with the appropriate permissions
#
# Globals:
#   INIT_NAMED_VOLUMES_SERVICE
#   _arg_enable_nginx_ssl
#   _arg_enable_postgres_ssl
#   _arg_plugins_branch
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

init_named_volumes() {
  local args=(
    "/scripts/init-named-volumes.sh"
    "--scripts-dir"
    "/scripts"
    "--clone-branch"
    "${_arg_plugins_branch}"
  )

  if [[ "${_arg_enable_nginx_ssl}" == "on" ]]; then
    args+=("--enable-nginx-ssl")
  fi

  if [[ "${_arg_enable_postgres_ssl}" == "on" ]]; then
    args+=("--enable-postgres-ssl")
  fi

  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" run \
    --rm \
    "${INIT_NAMED_VOLUMES_SERVICE}" \
    "${args[@]}"
}

###########################################################################################
# Wrapper for the init-minio.sh utility script
#
# Globals:
#   SCRIPT_DIRPATH
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

init_minio() {
  local script_path="${SCRIPT_DIRPATH}/scripts/init-minio.sh"

  if ! /usr/bin/env bash "${script_path}" "${SCRIPT_DIRPATH}"; then
    log_error "Encountered an error when executing ${script_path}, exiting..."
    exit 1
  fi
}

###########################################################################################
# The top-level function in the script
#
# Globals:
#   None
# Arguments:
#   Script arguments, an array
# Returns:
#   None
###########################################################################################

main() {
  parse_args "${@}"
  init_scripts
  init_extra_ca_certificates
  init_named_volumes
  init_minio
  start_db_service
  manage_postgres_ssl
  migrate_restapi_db
  stop_services
}

###########################################################################################
# Main script
###########################################################################################

main "${@}"
