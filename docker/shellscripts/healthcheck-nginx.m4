#!/bin/bash

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_POSITIONAL_INF([urls],[A list of URLs to healthcheck],[1])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Nginx healthcheck script\n])"
# ARGBASH_GO()

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

LOGNAME="Nginx Healthcheck"

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
# Check if a url returns a 200 or 401 status, raise an error if it doesn't
#
# Globals:
#   None
# Arguments:
#   URL to check, a string
# Returns:
#   None
###########################################################################################

check_url_status() {
  local url="${1}"
  local http_code
  local connect=()
  if [[ "${url}" == https://localhost:* ]]; then
    local identity="${DIOPTRA_PUBLIC_HOST:?DIOPTRA_PUBLIC_HOST is required}"
    if [[ "${identity}" == *:* ]]; then identity="[${identity}]"; fi
    url="${url/localhost/${identity}}"
    connect=(--noproxy '*' --connect-to '::127.0.0.1:')
  fi

  if ! http_code=$(curl --disable "${connect[@]}" -o /dev/null --silent --show-error -w "%{http_code}\n" "${url}"); then
    log_error "Polling of ${url} with curl failed."
    exit 1
  fi

  if [[ ! ("${http_code}" == "200" ||
    "${http_code}" == "301" ||
    "${http_code}" == "401" ||
    "${http_code}" == "403") ]]; then
    log_error "${url} returned status code ${http_code}."
    exit 1
  fi
}

###########################################################################################
# Check if all urls are healthy
#
# Globals:
#   _arg_urls
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

# Verify the configured public identity through loopback, without requiring a
# localhost SAN in supplied material. Only the API/UI health route uses this.
check_restapi_health() {
  local identity="${DIOPTRA_PUBLIC_HOST:?DIOPTRA_PUBLIC_HOST is required}"
  if [[ "${identity}" == *:* ]]; then
    identity="[${identity}]"
  fi
  local code
  code=$(curl --disable --fail --silent --show-error --noproxy '*' \
    --connect-to '::127.0.0.1:' \
    "https://${identity}:30443/health" -o /dev/null -w '%{http_code}')
  if [[ "${code}" != "200" ]]; then
    log_error "API HTTPS health returned status code ${code}."
    exit 1
  fi
}

healthcheck_urls() {
  for url in "${_arg_urls[@]}"; do
    check_url_status "${url}"
  done
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
  check_restapi_health
  healthcheck_urls
}

###########################################################################################
# Main script
###########################################################################################

main
# ] <-- needed because of Argbash
