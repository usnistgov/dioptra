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
# ARG_OPTIONAL_SINGLE([restapi-host],[],[Dioptra REST API Service host],[restapi])
# ARG_OPTIONAL_SINGLE([restapi-port],[],[Dioptra REST API Service port],[5000])
# ARG_OPTIONAL_SINGLE([mlflow-tracking-host],[],[MLflow Tracking Service host],[mlflow-tracking])
# ARG_OPTIONAL_SINGLE([mlflow-tracking-port],[],[MLflow Tracking Service port],[5000])
# ARG_OPTIONAL_SINGLE([nginx-restapi-port],[],[Nginx Dioptra REST API listening port],[30080])
# ARG_OPTIONAL_SINGLE([nginx-mlflow-port],[],[Nginx MLflow Tracking listening port],[35000])
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

readonly restapi_host="${_arg_restapi_host}"
readonly restapi_port="${_arg_restapi_port}"
readonly mlflow_tracking_host="${_arg_mlflow_tracking_host}"
readonly mlflow_tracking_port="${_arg_mlflow_tracking_port}"
readonly nginx_restapi_port="${_arg_nginx_restapi_port}"
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
#   mlflow_tracking_host
#   mlflow_tracking_port
#   nginx_restapi_port
#   nginx_mlflow_port
#   restapi_host
#   restapi_port
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

set_nginx_variables() {
  echo "${logname}: INFO - Set nginx variables  |  \
  MLFLOW_TRACKING_HOST=${mlflow_tracking_host} \
  MLFLOW_TRACKING_PORT=${mlflow_tracking_port} \
  NGINX_MLFLOW_PORT=${nginx_mlflow_port} \
  NGINX_RESTAPI_PORT=${nginx_restapi_port} \
  RESTAPI_HOST=${restapi_host} \
  RESTAPI_PORT=${restapi_port}"
  sed -i -e 's/$MLFLOW_TRACKING_HOST/'"${mlflow_tracking_host}"'/g' \
    /etc/nginx/conf.d/default.conf
  sed -i -e 's/$MLFLOW_TRACKING_PORT/'"${mlflow_tracking_port}"'/g' \
    /etc/nginx/conf.d/default.conf
  sed -i -e 's/$NGINX_MLFLOW_PORT/'"${nginx_mlflow_port}"'/g' /etc/nginx/conf.d/default.conf
  sed -i -e 's/$NGINX_RESTAPI_PORT/'"${nginx_restapi_port}"'/g' /etc/nginx/conf.d/default.conf
  sed -i -e 's/$RESTAPI_HOST/'"${restapi_host}"'/g' /etc/nginx/conf.d/default.conf
  sed -i -e 's/$RESTAPI_PORT/'"${restapi_port}"'/g' /etc/nginx/conf.d/default.conf

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
