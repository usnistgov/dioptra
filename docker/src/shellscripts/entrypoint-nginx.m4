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
# ARG_OPTIONAL_SINGLE([ai-lab-host],[],[AI Lab Service host],[restapi])
# ARG_OPTIONAL_SINGLE([ai-lab-port],[],[AI Lab Service port],[5000])
# ARG_OPTIONAL_SINGLE([mlflow-tracking-host],[],[AI Lab Service host],[mlflow-tracking])
# ARG_OPTIONAL_SINGLE([mlflow-tracking-port],[],[AI Lab Service port],[5000])
# ARG_OPTIONAL_SINGLE([nginx-lab-port],[],[Nginx listening port],[30080])
# ARG_OPTIONAL_SINGLE([nginx-mlflow-port],[],[Nginx listening port],[35000])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Nginx Entry Point\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly ai_lab_host="${_arg_ai_lab_host}"
readonly ai_lab_port="${_arg_ai_lab_port}"
readonly mlflow_tracking_host="${_arg_mlflow_tracking_host}"
readonly mlflow_tracking_port="${_arg_mlflow_tracking_port}"
readonly nginx_lab_port="${_arg_nginx_lab_port}"
readonly nginx_mlflow_port="${_arg_nginx_mlflow_port}"
readonly logname="Container Entry Point"

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
    echo "${logname}: ERROR - /usr/local/bin/secure-container.sh script missing" 1>&2
    exit 1
  fi
}

###########################################################################################
# Set nginx configuration variables
#
# Globals:
#   ai_lab_host
#   ai_lab_port
#   mlflow_tracking_host
#   mlflow_tracking_port
#   nginx_lab_port
#   nginx_mlflow_port
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

set_nginx_variables() {
  echo "${logname}: INFO - Set nginx variables  |  \
  AI_LAB_HOST=${ai_lab_host} \
  AI_LAB_PORT=${ai_lab_port} \
  MLFLOW_TRACKING_HOST=${mlflow_tracking_host} \
  MLFLOW_TRACKING_PORT=${mlflow_tracking_port} \
  NGINX_LAB_PORT=${nginx_lab_port}\
  NGINX_MLFLOW_PORT=${nginx_mlflow_port}"
  sed -i -e 's/$AI_LAB_HOST/'"${ai_lab_host}"'/g' /etc/nginx/conf.d/default.conf
  sed -i -e 's/$AI_LAB_PORT/'"${ai_lab_port}"'/g' /etc/nginx/conf.d/default.conf
  sed -i -e 's/$MLFLOW_TRACKING_HOST/'"${mlflow_tracking_host}"'/g' \
    /etc/nginx/conf.d/default.conf
  sed -i -e 's/$MLFLOW_TRACKING_PORT/'"${mlflow_tracking_port}"'/g' \
    /etc/nginx/conf.d/default.conf
  sed -i -e 's/$NGINX_LAB_PORT/'"${nginx_lab_port}"'/g' /etc/nginx/conf.d/default.conf
  sed -i -e 's/$NGINX_MLFLOW_PORT/'"${nginx_mlflow_port}"'/g' /etc/nginx/conf.d/default.conf

  local default_conf=$(cat /etc/nginx/conf.d/default.conf)
  echo "${logname}: INFO - Updated contents of /etc/nginx/conf.d/default.conf"
  echo "${default_conf}"
}

###########################################################################################
# Start nginx server
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_nginx() {
  echo "${logname}: INFO - Starting Nginx process"
  /usr/sbin/nginx
}

###########################################################################################
# Main script
###########################################################################################

secure_container
set_nginx_variables
start_nginx
# ] <-- needed because of Argbash
