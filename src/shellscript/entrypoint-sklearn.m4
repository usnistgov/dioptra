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
# ARG_OPTIONAL_SINGLE([conda-env],[],[Conda environment],[base])
# ARG_OPTIONAL_SINGLE([entry-point],[],[MLproject entry point to invoke],[main])
# ARG_OPTIONAL_SINGLE([s3-workflow],[],[S3 URI to a tarball or zip archive containing scripts and a MLproject file defining a workflow].[])
# ARG_LEFTOVERS([Entry point keyword arguments (optional)])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Securing AI Lab Entry Point\n])"
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
readonly mlflow_s3_endpoint_url="${MLFLOW_S3_ENDPOINT_URL-}"
readonly s3_workflow_uri="${_arg_s3_workflow}"

readonly workflow_filename="$(basename ${s3_workflow_uri} 2>/dev/null)"

###########################################################################################
# Install Python modules
#
# Globals:
#   ai_workdir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

install_python_modules() {
  local environment_file=$(find ${ai_workdir} -name environment.yml -type f -print)

  if [[ ! -z ${environment_file} && -f /usr/local/bin/install-python-modules.sh ]]; then
    echo "${logname}: environment.yml file found - ${environment_file}"
    /usr/local/bin/install-python-modules.sh ${environment_file}
  elif [[ ! -f /usr/local/bin/install-python-modules.sh ]]; then
    echo "${logname}: ERROR - install-python-modules.sh script missing"
    exit 1
  fi
}

###########################################################################################
# Restrict network access
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

restrict_network_access() {
  if [[ -f /usr/local/bin/install-python-modules.sh ]]; then
    /usr/local/bin/restrict-network-access.sh
  else
    echo "${logname}: ERROR - /usr/local/bin/restrict-network-access.sh script missing"
    exit 1
  fi
}

###########################################################################################
# Secure the container at runtime
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

secure_container() {
  if [[ -f /usr/local/bin/secure-container.sh ]]; then
    /usr/local/bin/secure-container.sh
  else
    echo "${logname}: ERROR - /usr/local/bin/secure-container.sh script missing"
    exit 1
  fi
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
  local filepath="${ai_workdir}/${workflow_filename}"

  if [[ -f ${filepath} && -f /usr/local/bin/unpack-archive.sh ]]; then
    /usr/local/bin/unpack-archive.sh --delete ${filepath}
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
  local dest="${ai_workdir}/${workflow_filename}"

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
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_mlflow() {
  local mlproject_file=$(find ${ai_workdir} -name MLproject -type f -print)

  if [[ -z ${mlproject_file} ]]; then
    echo "${logname}: ERROR - missing MLproject file"
    exit 1
  fi

  local mlproject_dir=$(dirname ${mlproject_file})

  echo "${logname}: mlproject file found - ${mlproject_file}"
  echo "${logname}: starting mlflow pipeline"
  echo "${logname}: mlflow run options - --no-conda -e ${entry_point} ${entry_point_kwargs}"

  bash -c "\
  source ${conda_dir}/etc/profile.d/conda.sh &&\
  conda activate ${conda_env} &&\
  cd ${ai_workdir} &&\
  mlflow run\
  --no-conda\
  -e ${entry_point}\
  ${entry_point_kwargs}\
  ${mlproject_dir}"
}

###########################################################################################
# Main script
###########################################################################################

s3_cp
unpack_archive
install_python_modules
secure_container
start_mlflow
# ] <-- needed because of Argbash
