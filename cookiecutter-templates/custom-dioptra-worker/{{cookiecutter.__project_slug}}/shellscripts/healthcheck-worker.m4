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

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Worker healthcheck script\n])"
# ARGBASH_GO()

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

CMD="python /opt/venv/bin/dioptra-worker-v1"
LOGNAME="Worker Healthcheck"

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
# Check if process is healthy
#
# Globals:
#   SHORT_CMD
#   LONG_CMD
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

__get_num_procs() {
  ps -ax | grep "${CMD}" | grep -v grep | wc -l
}

healthcheck_process() {
  local num_procs

  if ! num_procs="$(__get_num_procs)"; then
    log_error "Polling of ${$CMD} with ps failed."
    exit 1
  fi

  if ((num_procs != 1)); then
    log_error "Process count for ${CMD} is ${num_procs} instead of 1." 1>&2
    exit 1
  fi
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
  healthcheck_process
}

###########################################################################################
# Main script
###########################################################################################

main
# ] <-- needed because of Argbash
