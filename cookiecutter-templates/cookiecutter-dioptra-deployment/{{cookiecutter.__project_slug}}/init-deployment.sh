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
GENERATE_PASSWORD_TEMPLATES_SCRIPT="${SCRIPT_DIRPATH}/scripts/generate_password_templates.py"

CONTAINER_DB_PORT="5432"
SERVICE_WAIT_TIMEOUT_SECONDS=120

INIT_ARGBASH_SERVICE="argbash"
INIT_DB_SERVICE="db"
INIT_FRONTEND_SERVICE="frontend-build"
INIT_RC_SERVICE="rc"
INIT_RUSTFS_SERVICE="rustfs"
INIT_NAMED_VOLUMES_SERVICE="named-volumes"
INIT_RESTAPI_KEY_SERVICE="init-restapi-key"
INIT_RESTAPI_SERVICE="restapi"
INIT_WORKER_ACCOUNT_SERVICE="init-dioptra-worker"

DEFAULT_ARG_BRANCH="main"
DEFAULT_ARG_ENABLE_NGINX_SSL="on"
DEFAULT_ARG_ENABLE_POSTGRES_SSL="off"
DEFAULT_ARG_SKIP_RUSTFS_SETUP="off"
DEFAULT_ARG_PYTHON="$(command -v ${SCRIPT_DIRPATH}/.venv/bin/python 2 &>/dev/null && echo "${SCRIPT_DIRPATH}/.venv/bin/python" || echo "python")"
DEFAULT_ARG_WORKER_SSL_SERVICE="tfcpu"

_arg_branch="${DEFAULT_ARG_BRANCH}"
_arg_enable_nginx_ssl="${DEFAULT_ARG_ENABLE_NGINX_SSL}"
_arg_enable_postgres_ssl="${DEFAULT_ARG_ENABLE_POSTGRES_SSL}"
_arg_skip_rustfs_setup="${DEFAULT_ARG_SKIP_RUSTFS_SETUP}"
_arg_python="${DEFAULT_ARG_PYTHON}"
_arg_worker_ssl_service="${DEFAULT_ARG_WORKER_SSL_SERVICE}"

###########################################################################################
# Print the script help message
#
# Globals:
#   DEFAULT_ARG_BRANCH
#   DEFAULT_ARG_PYTHON
#   DEFAULT_ARG_WORKER_SSL_SERVICE
# . DEFAULT_ARG_SKIP_RUSTFS_SETUP
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
		                          [--skip-rustfs-setup] [--branch <arg>]
		                          [--worker-ssl-service [tfcpu|pytorchcpu]] [-h|--help]
		        --enable-nginx-ssl: Enable the SSL-enabled configuration settings for nginx image
		        --enable-postgres-ssl: Enable the SSL-enabled configuration settings for postgres
		                               image
		        --skip-rustfs-setup: Skip rustfs service setup. Useful when making configuration
		                            changes after initial deployment
		        --branch: The Dioptra GitHub branch to use when syncing the built-in task plugins
		                  and the frontend files (default: '${DEFAULT_ARG_BRANCH}')
		        --python: Command for invoking the Python interpreter. Must be Python 3.11 or
		                  greater, and the jinja2 package must be installed.
		                  (default: '${DEFAULT_ARG_PYTHON}')
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
# Validate the value passed to the --python argument
#
# Globals:
#   None
# Arguments:
#   Command for invoking the Python interpreter, a string
# Returns:
#   None
###########################################################################################

validate_python_cmd() {
  local candidate_python_cmd="${1}"

  if ! command -v "${candidate_python_cmd}" >/dev/null 2>&1; then
    log_error "Command \"${candidate_python_cmd}\" not found, exiting..."
    exit 1
  fi

  local jinja2_installed
  local jinja2_cmd_check=(
    "import"
    "importlib.util;"
    'print(importlib.util.find_spec("jinja2")'
    "is"
    "not"
    "None)"
  )
  if ! jinja2_installed="$("${candidate_python_cmd}" -c "${jinja2_cmd_check[*]}")"; then
    log_error "Command \"${candidate_python_cmd}\" -c \"${jinja2_cmd_check[*]}\"" \
      "failed, exiting..."
    exit 1
  fi

  if [[ "${jinja2_installed}" != "True" ]]; then
    log_error "The jinja2 package is not installed, exiting..."
    exit 1
  fi
}

###########################################################################################
# Validate the value passed to the --worker-ssl-service argument
#
# Globals:
#   None
# Arguments:
#   Worker SSL service, a string
# Returns:
#   None
###########################################################################################

validate_worker_ssl_service() {
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
#   _arg_branch
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
    --skip-rustfs-setup)
      _arg_skip_rustfs_setup="on"
      shift 1
      ;;
    --branch)
      _arg_branch="${2}"
      shift 2
      ;;
    --python)
      validate_python_cmd "${2}"
      _arg_python="${2}"
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
# Wrapper for invoking python
#
# Globals:
#   _arg_python
# Arguments:
#   Positional arguments, one or more strings
# Returns:
#   None
###########################################################################################

python_cmd() {
  if ! "${_arg_python}" "${@}"; then
    log_error "Encountered an error when executing python, exiting..."
    exit 1
  fi
}

###########################################################################################
# Wait for services to start
#
# Globals:
#   DOCKER_COMPOSE_INIT_YML
#   INIT_RESTAPI_SERVICE
#   SERVICE_WAIT_TIMEOUT_SECONDS
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
      "${SERVICE_WAIT_TIMEOUT_SECONDS}"
  done
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
# Starts a RustFS service as a background process
#
# Globals:
#   DOCKER_COMPOSE_INIT_YML
#   INIT_RUSTFS_SERVICE
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_rustfs_service() {
  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" up -d --wait --wait-timeout 180 "${INIT_RUSTFS_SERVICE}"
}

###########################################################################################
# Starts the restapi service as a background process
#
# Globals:
#   DOCKER_COMPOSE_INIT_YML
#   INIT_RESTAPI_SERVICE
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_restapi_service() {
  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" up -d "${INIT_RESTAPI_SERVICE}"
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
    "/scripts-src/init-frontend.sh"
    "/scripts-src/init-rustfs.sh"
    "/scripts-src/init-named-volumes.m4"
    "/scripts-src/init-worker-account.sh"
    "/scripts-src/init_worker_account.py"
    "/scripts-src/manage-postgres-ssl.m4"
    "/scripts-src/set-permissions.m4"
  )

  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" run \
    --rm \
    "${INIT_ARGBASH_SERVICE}" \
    "${args[@]}"
}

###########################################################################################
# Copy config files into the deployment's named volumes with the appropriate permissions
#
# Globals:
#   INIT_NAMED_VOLUMES_SERVICE
#   _arg_enable_nginx_ssl
#   _arg_enable_postgres_ssl
#   _arg_branch
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
    "${_arg_branch}"
  )

  args+=("--enable-nginx-ssl")

  if [[ "${_arg_enable_postgres_ssl}" == "on" ]]; then
    args+=("--enable-postgres-ssl")
  fi

  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" run \
    --rm \
    "${INIT_NAMED_VOLUMES_SERVICE}" \
    "${args[@]}"
}

###########################################################################################
# Initialize or preserve the API signing key before migrations and API startup
#
# Globals:
#   INIT_RESTAPI_KEY_SERVICE
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

init_restapi_key() {
  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" run \
    --rm \
    "${INIT_RESTAPI_KEY_SERVICE}"
}

###########################################################################################
# Wrapper for the init-rustfs.sh utility script
#
# Globals:
#   DOCKER_COMPOSE_INIT_YML
#   INIT_RC_SERVICE
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

init_rustfs() {
  local args=(
    "/scripts/init-rustfs.sh"
  )

  if [[ "${_arg_skip_rustfs_setup}" == "on" ]]; then
    return 0
  fi

  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" run \
    --rm \
    "${INIT_RC_SERVICE}" \
    "${args[@]}"
}

###########################################################################################
# Register the Dioptra worker user account
#
# Globals:
#   DOCKER_COMPOSE_INIT_YML
#   INIT_RESTAPI_SERVICE
#   INIT_WORKER_ACCOUNT_SERVICE
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

init_worker_account() {
  local args=(
    "/scripts/init-worker-account.sh"
  )

  wait_for_services "{{ cookiecutter.__project_slug }}-restapi:5000"

  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" run \
    --rm \
    "${INIT_WORKER_ACCOUNT_SERVICE}" \
    "${args[@]}"
}

###########################################################################################
# Wrapper for the generate_docker_templates.py and generate_password_templates.py utility
# scripts
#
# Globals:
#   GENERATE_PASSWORD_TEMPLATES_SCRIPT
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

init_templates() {
  python_cmd "${GENERATE_PASSWORD_TEMPLATES_SCRIPT}"
}

###########################################################################################
# Wrapper for the init-frontend.sh utility script
#
# Globals:
#   DOCKER_COMPOSE_INIT_YML
#   INIT_FRONTEND_SERVICE
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

init_frontend() {
  local args=(
    "/scripts/init-frontend.sh"
    "--output"
    "/frontend"
  )

  docker_compose -f "${DOCKER_COMPOSE_INIT_YML}" run \
    --rm \
    "${INIT_FRONTEND_SERVICE}" \
    "${args[@]}"
}

###########################################################################################
# Require the selected runtime containers to be absent before initialization.
#
# Globals:
#   SCRIPT_DIRPATH
# Arguments:
#   None
# Returns:
#   Exits nonzero if the deployment has not been torn down.
###########################################################################################

require_runtime_teardown() {
  PYTHONPATH="${SCRIPT_DIRPATH}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
    python_cmd -m ssl_support.preflight "${SCRIPT_DIRPATH}"
}

###########################################################################################
# Tear down services started for initialization without deleting persistent volumes.
#
# Globals:
#   DOCKER_COMPOSE_INIT_YML
# Arguments:
#   Whether initialization services are owned, on or off
#   Whether runtime services are owned, on or off
# Returns:
#   0 if both required teardowns succeed; 1 if either fails.
###########################################################################################

teardown_owned_services() {
  local init_services_owned="${1}" runtime_services_owned="${2}"
  local teardown_failed="off"

  if [[ "${runtime_services_owned}" == "on" ]]; then
    if ! {{ cookiecutter.docker_compose_path }} down; then
      log_error "Runtime teardown failed. Retain the deployment files and run {{ cookiecutter.docker_compose_path }} down before retrying."
      {{ cookiecutter.docker_compose_path }} stop || log_error "Runtime stop also failed."
      teardown_failed="on"
    fi
  fi
  if [[ "${init_services_owned}" == "on" ]]; then
    if ! {{ cookiecutter.docker_compose_path }} -f "${DOCKER_COMPOSE_INIT_YML}" down; then
      log_error "Initialization-service teardown failed. Retain the deployment files and tear down docker-compose.init.yml before retrying."
      {{ cookiecutter.docker_compose_path }} -f "${DOCKER_COMPOSE_INIT_YML}" stop || log_error "Initialization-service stop also failed."
      teardown_failed="on"
    fi
  fi

  # Attempt both teardowns before returning a failure.
  if [[ "${teardown_failed}" == "on" ]]; then
    return 1
  fi
}

###########################################################################################
# Run the EXIT cleanup and preserve the initialization failure status.
#
# Globals:
#   None
# Arguments:
#   Initialization exit status, an integer
#   Whether initialization services are owned, on or off
#   Whether runtime services are owned, on or off
# Returns:
#   Exits 1 if cleanup fails, otherwise exits with the incoming status.
###########################################################################################

finish_initialization() {
  local initialization_status="${1}" init_services_owned="${2}" runtime_services_owned="${3}"
  trap - EXIT

  if ! teardown_owned_services "${init_services_owned}" "${runtime_services_owned}"; then
    exit 1
  fi
  exit "${initialization_status}"
}

###########################################################################################
# Register cleanup with explicit ownership before a step can start services.
#
# Globals:
#   None
# Arguments:
#   Whether initialization services are owned, on or off
#   Whether runtime services are owned, on or off
# Returns:
#   None
###########################################################################################

set_initialization_cleanup() {
  # EXIT may run after Bash has unwound a failed function's locals. Capture the
  # ownership arguments now; expand the failure status only when the trap runs.
  local cleanup_command
  printf -v cleanup_command 'finish_initialization $? %q %q' "${1}" "${2}"
  trap "${cleanup_command}" EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
}

###########################################################################################
# Start the normal deployment for live verification and worker registration.
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   Exits nonzero if Compose cannot start the services.
###########################################################################################

start_runtime_services() {
  docker_compose up -d
}

###########################################################################################
# Wait for the API and require live verification of installed certificates.
#
# Globals:
#   SCRIPT_DIRPATH
# Arguments:
#   None
# Returns:
#   Exits nonzero if readiness or certificate validation fails.
###########################################################################################

validate_certificates() {
  wait_for_services "{{ cookiecutter.__project_slug }}-restapi:5000"
  python_cmd "${SCRIPT_DIRPATH}/scripts/manage_ssl.py" validate
}

###########################################################################################
# Prepare isolated public trust stores for setup-time downloads.
#
# Globals:
#   SCRIPT_DIRPATH
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

bootstrap_certificate_trust() {
  python_cmd "${SCRIPT_DIRPATH}/scripts/bootstrap_ssl_trust.py"
}

###########################################################################################
# Install and validate certificates offline without starting runtime services.
#
# Globals:
#   SCRIPT_DIRPATH
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

init_certificates() {
  python_cmd "${SCRIPT_DIRPATH}/scripts/manage_ssl.py" init
}

###########################################################################################
# Own setup services and clean them up on completion, failure or interruption.
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   Exits with the initialization status, or 1 if teardown fails.
###########################################################################################

initialize_deployment() {
  set_initialization_cleanup off off

  init_templates
  set_initialization_cleanup on off
  init_scripts
  bootstrap_certificate_trust
  init_named_volumes
  init_restapi_key
  start_rustfs_service
  init_rustfs
  stop_services
  init_frontend
  start_db_service
  manage_postgres_ssl
  stop_services
  init_certificates
  set_initialization_cleanup on on
  start_runtime_services
  validate_certificates
  init_worker_account
  finish_initialization 0 on on
}

###########################################################################################
# Parse options, check teardown prerequisites and initialize the deployment.
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
  require_runtime_teardown
  initialize_deployment
}

###########################################################################################
# Main script
###########################################################################################

main "${@}"
