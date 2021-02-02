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
# ARG_OPTIONAL_SINGLE([app-module],[],[Application module],[wsgi:app])
# ARG_OPTIONAL_SINGLE([backend],[],[Server backend],[gunicorn])
# ARG_OPTIONAL_SINGLE([conda-env],[],[Conda environment],[mitre-securing-ai])
# ARG_OPTIONAL_ACTION([upgrade-db],[],[Upgrade the database schema],[upgrade_database])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Securing AI Lab API Entry Point\n])"
# ARGBASH_PREPARE

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly ai_workdir="${AI_WORKDIR}"
readonly conda_dir="${CONDA_DIR}"
readonly logname="Container Entry Point"

set_parsed_globals() {
  readonly app_module="${_arg_app_module}"
  readonly conda_env="${_arg_conda_env}"
  readonly server_backend="${_arg_backend}"
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
# Upgrade the Securing AI database
#
# Globals:
#   ai_workdir
#   conda_dir
#   conda_env
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

upgrade_database() {
  echo "${logname}: INFO - Upgrading the Securing AI database"

  set_parsed_globals

  bash -c "\
  source ${conda_dir}/etc/profile.d/conda.sh &&\
  conda activate ${conda_env} &&\
  cd ${ai_workdir} &&\
  flask db upgrade -d ${ai_workdir}/migrations"
}

###########################################################################################
# Start gunicorn server
#
# Globals:
#   ai_workdir
#   app_module
#   conda_dir
#   conda_env
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_gunicorn() {
  echo "${logname}: INFO - Starting gunicorn server"

  bash -c "\
  source ${conda_dir}/etc/profile.d/conda.sh &&\
  conda activate ${conda_env} &&\
  cd ${ai_workdir} &&\
  gunicorn -c /etc/gunicorn/gunicorn.conf.py ${app_module}"
}

###########################################################################################
# Start RESTful API service
#
# Globals:
#   logname
#   server_backend
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_restapi() {
  case ${server_backend} in
    gunicorn)
      start_gunicorn
      ;;
    *)
      echo "${logname}: ERROR - unsupported backend - ${server_backend}" 1>&2
      exit 1
      ;;
  esac
}

###########################################################################################
# Main script
###########################################################################################

parse_commandline "$@"
set_parsed_globals
secure_container
start_restapi
# ] <-- needed because of Argbash
