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
# ARG_OPTIONAL_REPEATED([wait-for],[],[Wait on the availability of a host and TCP port before proceeding],[])
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

readonly logname="Container Entry Point"

###########################################################################################
# Wait for services to start
#
# Globals:
#   _arg_wait_for
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

wait_for_services() {
  for service in ${_arg_wait_for[@]}; do
    if ! (/usr/local/bin/wait-for-it.sh -t 0 ${service}); then
      echo "${logname}: ERROR - Unexpected error while waiting for ${service}." 1>&2
      exit 1
    fi
  done
}

###########################################################################################
# Start nginx server
#
# Globals:
#   logname
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

wait_for_services
start_nginx
# ] <-- needed because of Argbash
