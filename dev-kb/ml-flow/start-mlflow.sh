#!/usr/bin/env bash

shopt -s extglob
set -eo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

SCRIPT_CMDNAME="${0##*/}"
SCRIPT_DIRPATH="$(realpath ${0%%/*})"
LOGNAME="MLflow Tracking Server (Dev)"

MLFLOW_COMMAND="mlflow"

DEFAULT_ARG_HOST="127.0.0.1"
DEFAULT_ARG_PORT="35000" 
DEFAULT_ARG_ARTIFACTS_DESTINATION="mlflow/runs"
DEFAULT_ARG_BACKEND_STORE_URI="sqlite:///mlflow/mlflow.sqlite"
DEFAULT_ARG_UPGRADE_DB="off"

_arg_host="${DEFAULT_ARG_HOST}"
_arg_port="${DEFAULT_ARG_PORT}"
_arg_artifacts_destination="${DEFAULT_ARG_ARTIFACTS_DESTINATION}"
_arg_backend_store_uri="${DEFAULT_ARG_BACKEND_STORE_URI}"
_arg_upgrade_db="${DEFAULT_ARG_UPGRADE_DB}"

###########################################################################################
# Print the script help message
#
# Globals:
#   DEFAULT_ARG_HOST
#   DEFAULT_ARG_PORT
#   DEFAULT_ARG_ARTIFACTS_DESTINATION
#   DEFAULT_ARG_BACKEND_STORE_URI
# Arguments:
#   Error messages to log, a string
# Returns:
#   None
###########################################################################################

print_help() {
  src_path="${BASH_SOURCE[0]}"
  this_name=$(basename "$src_path")

  cat <<-HELPMESSAGE
		Start a MLflow Tracking server for local development.

		Note: The parent folder(s) specified in --backend-store-uri and --artifacts-destination
		options must exist before starting this script. If using the default choices, then you
		need to create a "mlflow" folder in your current working directory, e.g. \`mkdir mlflow\`.

		Usage: "${this_name}" [--host <arg>] [--port <arg>] [--artifacts-destination <arg>] [--backend-store-uri <arg>] [-h|--help]
		        --host: Tag to give to built image (default: '${DEFAULT_ARG_HOST}')
		        --port: Tag to give to built image (default: '${DEFAULT_ARG_PORT}')
		        --artifacts-destination: The URI to use for storing MLflow run artifacts.
		                                 (default: '${DEFAULT_ARG_ARTIFACTS_DESTINATION}')
		        --backend-store-uri: The URI to use for storing MLflow run metadata.
		                             (default: '${DEFAULT_ARG_BACKEND_STORE_URI}')
		        --upgrade-db: If set, attempt to migrate the MLflow Tracking database before
		                      starting the server.
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
# Wrapper for invoking mlflow
#
# Globals:
#   MLFLOW_COMMAND
# Arguments:
#   Positional arguments, one or more strings
# Returns:
#   None
###########################################################################################

mlflow_cmd() {
  if ! "${MLFLOW_COMMAND}" "${@}"; then
    log_error "Encountered an error when executing ${MLFLOW_COMMAND}, exiting..."
    exit 1
  fi
}


###########################################################################################
# Create directories in the path
#
# Globals: None
# Arguments:
#   Script argument - path to create
# Returns:
#   None
###########################################################################################
create_path_if_needed(){
    __path=''
    if [ $# -lt 1 ]; then
      __path="${_arg_artifacts_destination}"
      echo "Missing path argument, using _arg_artifacts_destination=$(__path)";
    else
      __path="$1"
    fi
    if [ ! -e "$__path" ]; then
        echo "Creating path: ${__path@Q} "
        mkdir -p "$__path"
    else
        echo "Path: ${__path@Q} exists already"
    fi
}

###########################################################################################
# Parse the script arguments
#
# Globals:
#   _arg_host
#   _arg_port
#   _arg_artifacts_destination
#   _arg_backend_store_uri
#   _arg_upgrade_db
# Arguments:
#   Script arguments, an array
# Returns:
#   None
###########################################################################################

parse_args() {
  while (( "${#}" > 0)); do
    case "${1}" in
      -h | --help)
        print_help
        exit 0
        ;;
      --host)
        _arg_host="${2}"
        shift 2
        ;;
      --port)
        _arg_port="${2}"
        shift 2
        ;;
      --artifacts-destination)
        _arg_artifacts_destination="${2}"
        shift 2
        ;;
      --backend-store-uri)
        _arg_backend_store_uri="${2}"
        shift 2
        ;;
      --upgrade-db)
        _arg_upgrade_db="on"
        shift 1
        ;;
      *)
        log_error "Unrecognized argument ${1}, exiting..."
        exit 1
        ;;
    esac
  done
}

###########################################################################################
# Upgrade the MLFlow Tracking database
#
# Globals:
#   _arg_upgrade_db
#   _arg_backend_store_uri
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

upgrade_database() {
  if [[ "${_arg_upgrade_db}" != "on" ]]; then
    return 0
  fi

  log_info "Upgrading the MLFlow Tracking database"
  mlflow_cmd db upgrade "${_arg_backend_store_uri}"
}

###########################################################################################
# Start MLFlow Tracking server
#
# Globals:
#   _arg_host
#   _arg_port
#   _arg_artifacts_destination
#   _arg_backend_store_uri
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_mlflow_server() {
  log_info "Starting MLflow Tracking server"

  mlflow_cmd server \
    --host "${_arg_host}" \
    --port "${_arg_port}" \
    --artifacts-destination "${_arg_artifacts_destination}" \
    --backend-store-uri "${_arg_backend_store_uri}"
}

###########################################################################################
# The top-level function in the script
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

main() {
  parse_args "${@}"
  create_path_if_needed "${_arg_artifacts_destination}"
  upgrade_database
  start_mlflow_server
}

###########################################################################################
# Main script
###########################################################################################

main "${@}"
