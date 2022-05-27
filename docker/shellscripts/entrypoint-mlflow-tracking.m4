#!/bin/bash
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

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_OPTIONAL_SINGLE([conda-env],[],[Conda environment],[dioptra])
# ARG_OPTIONAL_SINGLE([backend-store-uri],[],[URI to which to persist experiment and run data. Acceptable URIs are\nSQLAlchemy-compatible database connection strings (e.g. 'sqlite:///path/to/file.db')\nor local filesystem URIs (e.g. 'file:///absolute/path/to/directory').],[sqlite:////work/mlruns/mlflow-tracking.db])
# ARG_OPTIONAL_SINGLE([default-artifact-root],[],[Local or S3 URI to store artifacts, for new experiments. Note that this flag does\nnot impact already-created experiments. Default: Within file store, if a file:/\nURI is provided. If a sql backend is used, then this option is required.],[file:///work/artifacts])
# ARG_OPTIONAL_SINGLE([gunicorn-opts],[],[Additional command line options forwarded to gunicorn processes.],[])
# ARG_OPTIONAL_SINGLE([host],[],[The network address to listen on. Use 0.0.0.0 to bind to all addresses if you want to access the tracking server from other machines.],[0.0.0.0])
# ARG_OPTIONAL_SINGLE([output],[o],[Path to save exported environment.yml file (ignored unless paired with --export-conda-env)],[])
# ARG_OPTIONAL_SINGLE([port],[],[The port to listen on.],[5000])
# ARG_OPTIONAL_SINGLE([workers],[],[Number of gunicorn worker processes to handle requests.],[4])
# ARG_OPTIONAL_ACTION([export-conda-env],[],[Freeze and export the container's conda environment (--output must be set)],[export_conda_environment])
# ARG_OPTIONAL_ACTION([upgrade-db],[],[Upgrade the database schema],[upgrade_database])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([MLFlow Tracking Server Entry Point\n])"
# ARGBASH_PREPARE

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly conda_dir="${CONDA_DIR}"
readonly mlflow_s3_endpoint_url="${MLFLOW_S3_ENDPOINT_URL-}"
readonly logname="Container Entry Point"

set_parsed_globals() {
  readonly backend_store_uri="${_arg_backend_store_uri}"
  readonly conda_env="${_arg_conda_env}"
  readonly default_artifact_root="${_arg_default_artifact_root}"
  readonly gunicorn_opts="${_arg_gunicorn_opts}"
  readonly host_address="${_arg_host}"
  readonly port="${_arg_port}"
  readonly workers="${_arg_workers}"
}

###########################################################################################
# Secure the container at runtime
#
# Globals:
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

secure_container() {
  if [[ -f /usr/local/bin/secure-container.sh ]]; then
    /usr/local/bin/secure-container.sh
  else
    echo "${logname}: ERROR - /usr/local/bin/secure-container.sh script missing" 1>&2
    exit 1
  fi
}

###########################################################################################
# Create bucket on S3 storage
#
# Globals:
#   default_artifact_root
#   mlflow_s3_endpoint_url
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

s3_mb() {
  local proto=$(echo ${default_artifact_root} | grep :// | sed -e "s,^\(.*://\).*,\1,g")
  local url=$(echo ${default_artifact_root/${proto}/})

  echo "${logname}: artifacts storage backend protocol is ${proto}"

  if [[ ${proto} == s3:// && ! -z ${mlflow_s3_endpoint_url} && -f /usr/local/bin/s3-mb.sh ]]; then
    local bucket=${url%%/*}
    echo "${logname}: artifacts storage path is ${default_artifact_root}, ensuring bucket ${bucket} exists"
    /usr/local/bin/s3-mb.sh --endpoint-url ${mlflow_s3_endpoint_url} ${bucket}
  elif [[ ${proto} == s3:// && -z ${mlflow_s3_endpoint_url} && -f /usr/local/bin/s3-mb.sh ]]; then
    local bucket=${url%%/*}
    echo "${logname}: artifacts storage path is ${default_artifact_root}, ensuring bucket ${bucket} exists"
    /usr/local/bin/s3-mb.sh ${bucket}
  elif [[ ! -f /usr/local/bin/s3-mb.sh ]]; then
    echo "${logname}: ERROR - /usr/local/bin/s3-mb.sh script missing" 1>&2
    exit 1
  else
    echo "${logname}: artifacts storage path is ${default_artifact_root}"
  fi
}

###########################################################################################
# Freeze and export the container's conda virtual environment
#
# Globals:
#   conda_env
#   logname
#   _arg_output
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

export_conda_environment() {
  if [[ ! -f /usr/local/bin/conda-env.sh ]]; then
    echo "${logname}: ERROR - /usr/local/bin/conda-env.sh script missing" 1>&2
    exit 1
  fi

  set_parsed_globals

  if ! /usr/local/bin/conda-env.sh --env ${conda_env} --output ${_arg_output} --freeze; then
    exit 1
  fi
}

###########################################################################################
# Upgrade the MLFlow Tracking database
#
# Globals:
#   backend_store_uri
#   conda_dir
#   conda_env
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

upgrade_database() {
  echo "${logname}: INFO - Upgrading the MLFlow Tracking database"

  set_parsed_globals

  bash -c "\
  source ${conda_dir}/etc/profile.d/conda.sh &&\
  conda activate ${conda_env} &&\
  mlflow db upgrade ${backend_store_uri}"
}

###########################################################################################
# Start MLFlow Tracking server
#
# Globals:
#   backend_store_uri
#   conda_dir
#   conda_env
#   default_artifact_root
#   gunicorn_opts
#   host_address
#   logname
#   port
#   workers
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_mlflow_server() {
  local optional_kwargs=""

  if [[ ! -z ${gunicorn_opts} ]]; then
    optional_kwargs="${optional_kwargs} --gunicorn-opts ${gunicorn_opts}"
  fi

  echo "${logname}: starting mlflow tracking server"
  echo "${logname}: mlflow server options -\
    --backend-store-uri ${backend_store_uri}\
    --default-artifact-root ${default_artifact_root}\
    --host ${host_address}\
    --port ${port}\
    --workers ${workers}\
    ${optional_kwargs}" |
    tr -s "[:blank:]"

  bash -c "\
  source ${conda_dir}/etc/profile.d/conda.sh &&\
  conda activate ${conda_env} &&\
  mlflow server\
    --backend-store-uri ${backend_store_uri}\
    --default-artifact-root ${default_artifact_root}\
    --host ${host_address}\
    --port ${port}\
    --workers ${workers}\
    ${optional_kwargs}"
}

###########################################################################################
# Main script
###########################################################################################

parse_commandline "$@"
set_parsed_globals
secure_container
s3_mb
start_mlflow_server
# ] <-- needed because of Argbash
