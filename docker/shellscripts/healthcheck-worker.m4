#!/bin/bash

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

SHORT_CMD="python"
LONG_CMD="python -m dioptra.rq.cli.rq worker"
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
  ps -C "${SHORT_CMD}" --no-headers -o cmd | grep -E "^${LONG_CMD}" | wc -l
}

healthcheck_process() {
  local num_procs

  if ! num_procs="$(__get_num_procs)"; then
    log_error "Polling of ${_arg_cmd} with ps failed."
    exit 1
  fi

  if ((num_procs != 1)); then
    log_error "Process count for ${_arg_cmd} is ${num_procs} instead of 1." 1>&2
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
