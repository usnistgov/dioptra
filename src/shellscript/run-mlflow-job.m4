#!/bin/bash
# Script adapted from the work https://github.com/jupyter/docker-stacks/blob/56e54a7320c3b002b8b136ba288784d3d2f4a937/base-notebook/start.sh.
# See copyright below.
#
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# Neither the name of the Jupyter Development Team nor the names of its
# contributors may be used to endorse or promote products derived from this
# software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_OPTIONAL_SINGLE([backend],[],[[securingai|local] Execution backend for MLFlow],[securingai])
# ARG_OPTIONAL_SINGLE([conda-env],[],[Conda environment],[base])
# ARG_OPTIONAL_SINGLE([experiment-id],[],[ID of the experiment under which to launch the run],[])
# ARG_OPTIONAL_SINGLE([entry-point],[],[MLproject entry point to invoke],[main])
# ARG_OPTIONAL_SINGLE([s3-workflow],[],[S3 URI to a tarball or zip archive containing scripts and a MLproject file defining a workflow],[])
# ARG_LEFTOVERS([Entry point keyword arguments (optional)])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Execute a job defined in a MLproject file.\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly ai_workdir="${AI_WORKDIR}"
readonly conda_dir="${CONDA_DIR}"
readonly conda_env="${_arg_conda_env}"
readonly entry_point_kwargs="${_arg_leftovers[*]}"
readonly entry_point="${_arg_entry_point}"
readonly logname="Container Entry Point"
readonly mlflow_backend="${_arg_backend}"
readonly mlflow_experiment_id="${_arg_experiment_id}"
readonly mlflow_s3_endpoint_url="${MLFLOW_S3_ENDPOINT_URL-}"
readonly s3_workflow_uri="${_arg_s3_workflow}"

readonly workflow_filename="$(basename ${s3_workflow_uri} 2>/dev/null)"

###########################################################################################
# Validate MLFlow-related option flags
#
# Globals:
#   logname
#   mlflow_backend
#   mlflow_experiment_id
#   mlflow_s3_endpoint_url
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_mlflow_inputs() {
  [[ ! -z ${mlflow_experiment_id} ]] ||
    echo "${logname}: ERROR - --experiment-id option not set" ||
    exit 1

  [[ ! -z ${mlflow_s3_endpoint_url} ]] ||
    echo "${logname}: ERROR - MLFLOW_S3_ENDPOINT_URL environment variable not set" ||
    exit 1

  case ${mlflow_backend} in
    securingai | local) ;;
    *)
      echo "${logname}: ERROR - --backend option must be \"securingai\" or \"local\""
      exit 1
      ;;
  esac
}

###########################################################################################
# Unpack an archive
#
# Globals:
#   ai_workdir
#   workflow_filename
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

unpack_archive() {
  local filepath="$(pwd)/${workflow_filename}"

  if [[ -f ${filepath} && -f /usr/local/bin/unpack-archive.sh ]]; then
    /usr/local/bin/unpack-archive.sh ${filepath}
  elif [[ ! -f /usr/local/bin/unpack-archive.sh ]]; then
    echo "${logname}: ERROR - /usr/local/bin/unpack-archive.sh script missing"
    exit 1
  elif [[ ! -f ${filepath} ]]; then
    echo "${logname}: ERROR - workflow archive file missing"
    exit 1
  fi
}

###########################################################################################
# Copy file to/from S3 storage
#
# Globals:
#   ai_workdir
#   mlflow_s3_endpoint_url
#   s3_workflow_uri
#   workflow_filename
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

s3_cp() {
  local src="${s3_workflow_uri}"
  local dest="$(pwd)/${workflow_filename}"

  if [[ ! -z ${mlflow_s3_endpoint_url} && -f /usr/local/bin/s3-cp.sh ]]; then
    /usr/local/bin/s3-cp.sh --endpoint-url ${mlflow_s3_endpoint_url} ${src} ${dest}
  elif [[ -z ${mlflow_s3_endpoint_url} && -f /usr/local/bin/s3-cp.sh ]]; then
    /usr/local/bin/s3-cp.sh ${src} ${dest}
  elif [[ ! -f /usr/local/bin/s3-cp.sh ]]; then
    echo "${logname}: ERROR - /usr/local/bin/s3-cp.sh script missing"
    exit 1
  fi
}

###########################################################################################
# Start MLFlow pipeline defined in MLproject file
#
# Globals:
#   ai_workdir
#   conda_dir
#   conda_env
#   entry_point
#   entry_point_kwargs
#   mlflow_backend
#   mlflow_experiment_id
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_mlflow() {
  local workflow_filepath="$(pwd)/${workflow_filename}"
  local mlflow_backend_opts="--backend ${mlflow_backend}\
  --backend-config {\"workflow_filepath\":\"${workflow_filepath}\"}"
  local mlproject_file=$(find ${ai_workdir} -name MLproject -type f -print)

  if [[ -z ${mlproject_file} ]]; then
    echo "${logname}: ERROR - missing MLproject file"
    exit 1
  fi

  local mlproject_dir=$(dirname ${mlproject_file})

  echo "${logname}: mlproject file found - ${mlproject_file}"
  echo "${logname}: starting mlflow pipeline"
  echo "${logname}: mlflow run options - --no-conda ${mlflow_backend_opts}\
  --experiment-id ${mlflow_experiment_id} -e ${entry_point} ${entry_point_kwargs}"

  mlflow run --no-conda \
    ${mlflow_backend_opts} \
    --experiment-id ${mlflow_experiment_id} \
    -e ${entry_point} \
    ${entry_point_kwargs} \
    ${mlproject_dir}
}

###########################################################################################
# Main script
###########################################################################################

validate_mlflow_inputs
s3_cp
unpack_archive
start_mlflow
# ] <-- needed because of Argbash
