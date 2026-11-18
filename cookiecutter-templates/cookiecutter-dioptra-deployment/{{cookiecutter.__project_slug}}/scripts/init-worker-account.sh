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

shopt -s extglob
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

LOGNAME="Init Worker Account"
RESTAPI_USERS_URL="http://restapi:5000/api/v1/users/"

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
# Register the Dioptra worker user account with the REST API
#
# The users endpoint answers 200 when it creates the account and 409 when the username is
# already taken, which is the case when the deployment is initialized again. Any other
# answer, or no answer at all, stops the initialization so that a deployment is never
# left without a worker account.
#
# Globals:
#   DIOPTRA_WORKER_PASSWORD
#   DIOPTRA_WORKER_USERNAME
#   RESTAPI_USERS_URL
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

register_worker_account() {
  local response
  local status
  local body

  if ! response="$(
    curl --silent --show-error -X POST "${RESTAPI_USERS_URL}" \
      -H 'Content-Type: application/json' \
      -w '\n%{http_code}' \
      -d "{\"username\": \"$DIOPTRA_WORKER_USERNAME\",
              \"password\": \"$DIOPTRA_WORKER_PASSWORD\",
              \"confirmPassword\": \"$DIOPTRA_WORKER_PASSWORD\"}"
  )"; then
    log_error "Could not reach the REST API at ${RESTAPI_USERS_URL}, exiting..."
    exit 1
  fi

  status="${response##*$'\n'}"
  body="${response%$'\n'*}"

  case "${status}" in
    2??)
      log_info "Registered the worker account ${DIOPTRA_WORKER_USERNAME}"
      ;;
    409)
      log_info "The worker account ${DIOPTRA_WORKER_USERNAME} already exists," \
        "its password was not changed"
      ;;
    *)
      log_error "Registering the worker account ${DIOPTRA_WORKER_USERNAME} failed" \
        "with HTTP status ${status}: ${body}"
      exit 1
      ;;
  esac
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
  register_worker_account
}

###########################################################################################
# Main script
###########################################################################################

main
