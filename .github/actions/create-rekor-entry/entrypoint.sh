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

shopt -s extglob
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

LOGNAME="Create Rekor Entry Entrypoint"

PAYLOAD_FILENAME="payload.json"
PUBLIC_KEY_FILENAME="public.pub"
REKOR_PAYLOAD_FILENAME="rekor_payload.json"
REKOR_RESPONSE_FILENAME="rekor_response.json"

TEMP_DIR="$(mktemp -d)"

_arg_payload=""
_arg_public_key=""
_arg_signature=""

###########################################################################################
# Print the script help message
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

print_help() {
  cat <<-HELPMESSAGE
		Create a Rekor entry for a signed image payload.

		Usage: entrypoint.sh [--payload <arg>] [--public-key <arg>]
		                     [--signature <arg>] [-h|--help]
		        --payload: The payload that was signed (required)
		        --public-key: The public key for verifying the payload signature (required)
		        --signature: The base64-encoded OpenSSL signature for the payload (required)
		        -h, --help: Prints help
	HELPMESSAGE
}

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
  echo "${LOGNAME}: INFO -" "${@}" 1>&2
}

###########################################################################################
# Validate payload variable is not empty
#
# Globals:
#   _arg_payload
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_payload_provided() {
  if [[ -z "${_arg_payload}" ]]; then
    log_error "A payload was not provided, exiting..."
    exit 1
  fi
}

###########################################################################################
# Validate public key variable is not empty
#
# Globals:
#   _arg_public_key
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_public_key_provided() {
  if [[ -z "${_arg_public_key}" ]]; then
    log_error "A public key was not provided, exiting..."
    exit 1
  fi
}

###########################################################################################
# Validate signature variable is not empty
#
# Globals:
#   _arg_signature
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_signature_provided() {
  if [[ -z "${_arg_signature}" ]]; then
    log_error "A signature was not provided, exiting..."
    exit 1
  fi
}

###########################################################################################
# Get the path to payload file
#
# Globals:
#   PAYLOAD_FILENAME
#   TEMP_DIR
# Arguments:
#   None
# Returns:
#   The full path for the payload file, a string
###########################################################################################

get_payload_path() {
  # Remove a trailing slash if present
  local dir_prefix="${TEMP_DIR%/}"

  # Remove a leading slash if present
  local filename="${PAYLOAD_FILENAME#/}"

  # Return full path to the payload file
  echo "${dir_prefix}/${filename}"
}

###########################################################################################
# Get the path to the public key file
#
# Globals:
#   PUBLIC_KEY_FILENAME
#   TEMP_DIR
# Arguments:
#   None
# Returns:
#   The full path for the public key file, a string
###########################################################################################

get_public_key_path() {
  # Remove a trailing slash if present
  local dir_prefix="${TEMP_DIR%/}"

  # Remove a leading slash if present
  local filename="${PUBLIC_KEY_FILENAME#/}"

  # Return full path to the public key file
  echo "${dir_prefix}/${filename}"
}

###########################################################################################
# Get the path to Rekor payload file
#
# Globals:
#   REKOR_PAYLOAD_FILENAME
#   TEMP_DIR
# Arguments:
#   None
# Returns:
#   The full path for the payload file, a string
###########################################################################################

get_rekor_payload_path() {
  # Remove a trailing slash if present
  local dir_prefix="${TEMP_DIR%/}"

  # Remove a leading slash if present
  local filename="${REKOR_PAYLOAD_FILENAME#/}"

  # Return full path to the Rekor payload file
  echo "${dir_prefix}/${filename}"
}

###########################################################################################
# Get the path to Rekor response file
#
# Globals:
#   REKOR_RESPONSE_FILENAME
#   TEMP_DIR
# Arguments:
#   None
# Returns:
#   The full path for the response file, a string
###########################################################################################

get_rekor_response_path() {
  # Remove a trailing slash if present
  local dir_prefix="${TEMP_DIR%/}"

  # Remove a leading slash if present
  local filename="${REKOR_RESPONSE_FILENAME#/}"

  # Return full path to the Rekor response file
  echo "${dir_prefix}/${filename}"
}

###########################################################################################
# Wrapper for invoking base64
#
# Globals:
#   None
# Arguments:
#   Positional arguments, one or more strings
# Returns:
#   The command's output
###########################################################################################

base64_cmd() {
  if ! base64 "${@}"; then
    log_error "Encountered an error when executing base64, exiting..."
    exit 1
  fi
}

###########################################################################################
# Wrapper for invoking curl
#
# Globals:
#   None
# Arguments:
#   Positional arguments, one or more strings
# Returns:
#   The command's output
###########################################################################################

curl_cmd() {
  if ! curl "${@}"; then
    log_error "Encountered an error when executing base64, exiting..."
    exit 1
  fi
}

###########################################################################################
# Wrapper for invoking grep
#
# Globals:
#   None
# Arguments:
#   Positional arguments, one or more strings
# Returns:
#   The command's output
###########################################################################################

grep_cmd() {
  if ! grep "${@}"; then
    log_error "Encountered an error when executing grep, exiting..."
    exit 1
  fi
}

###########################################################################################
# Wrapper for invoking jq
#
# Globals:
#   None
# Arguments:
#   Positional arguments, one or more strings
# Returns:
#   The command's output
###########################################################################################

jq_cmd() {
  if ! jq "${@}"; then
    log_error "Encountered an error when executing jq, exiting..."
    exit 1
  fi
}

###########################################################################################
# Wrapper for invoking sha256sum
#
# Globals:
#   None
# Arguments:
#   Positional arguments, one or more strings
# Returns:
#   The command's output
###########################################################################################

sha256sum_cmd() {
  if ! sha256sum "${@}"; then
    log_error "Encountered an error when executing sha256sum, exiting..."
    exit 1
  fi
}

###########################################################################################
# Parse the script arguments
#
# Globals:
#   _arg_payload
#   _arg_public_key
#   _arg_signature
# Arguments:
#   Script arguments, an array
# Returns:
#   None
###########################################################################################

parse_args() {
  while (("${#}" > 0)); do
    case "${1}" in
      -h | --help)
        print_help
        exit 0
        ;;
      --payload)
        _arg_payload="${2}"
        shift 2
        ;;
      --public-key)
        _arg_public_key="${2}"
        shift 2
        ;;
      --signature)
        _arg_signature="${2}"
        shift 2
        ;;
      *)
        log_error "Unrecognized argument ${1}, exiting..."
        exit 1
        ;;
    esac
  done
}

###########################################################################################
# Save payload to a file
#
# Globals:
#   _arg_payload
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

save_payload_to_file() {
  validate_payload_provided

  local payload_path="$(get_payload_path)"

  if ! echo -n "${_arg_payload}" > "${payload_path}"; then
    log_error "Encountered an error when saving the payload to ${payload_path}," \
      "exiting..."
    exit 1
  fi
}

###########################################################################################
# Save public key to a file
#
# Globals:
#   _arg_public_key
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

save_public_key_to_file() {
  validate_public_key_provided

  local public_key_path="$(get_public_key_path)"

  if ! echo "${_arg_public_key}" > "${public_key_path}"; then
    log_error "Encountered an error when saving the public key to ${public_key_path}," \
      "exiting..."
    exit 1
  fi
}

###########################################################################################
# base64 encode a file
#
# Globals:
#   None
# Arguments:
#   Path to file, a string
# Returns:
#   The base64-encoded file content
###########################################################################################

base64_encode() {
  local filepath="${1}"

  if ! base64_cmd "--wrap=0" < "${filepath}" | tr -d '\n'; then
    log_error "Encountered an error when encoding the file ${filepath}," \
      "exiting..."
    exit 1
  fi
}

###########################################################################################
# Checksum a file using sha256
#
# Globals:
#   None
# Arguments:
#   Path to file, a string
# Returns:
#   The sha256 file hash
###########################################################################################

checksum_file() {
  local filepath="${1}"

  if ! sha256sum_cmd < "${filepath}" | cut -d ' ' -f1; then
    log_error "Encountered an error when checksumming the file," \
      "exiting..."
    exit 1
  fi
}

###########################################################################################
# Validate a the Rekor UUID
#
# Globals:
#   None
# Arguments:
#   Rekor UUID to validate, a string
# Returns:
#   None
###########################################################################################

validate_rekor_uuid() {
  local rekor_uuid="${1}"

  if [[ ! "${rekor_uuid}" =~ ^[a-f0-9]{64,}$ ]]; then
    log_error "${rekor_uuid} is not a valid Rekor UUID, exiting..."
    exit 1
  fi
}

###########################################################################################
# Build the Rekor payload and write to disk
#
# Globals:
#   _arg_signature
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

save_rekor_payload() {
  local payload_filepath="$(get_payload_path)"
  local rekor_payload_filepath="$(get_rekor_payload_path)"
  local public_key_filepath="$(get_public_key_path)"

  local payload_checksum="$(checksum_file ${payload_filepath})"
  local public_key_b64="$(base64_encode ${public_key_filepath})"

  cat <<-REKOR_PAYLOAD > "${rekor_payload_filepath}"
		{
		  "apiVersion": "0.0.1",
		  "kind": "hashedrekord",
		  "spec": {
		      "data": {
		          "hash": {
		              "algorithm": "sha256",
		              "value": "${payload_checksum}"
		          }
		      },
		      "signature": {
		          "content": "${_arg_signature}",
		          "publicKey": {
		              "content": "${public_key_b64}"
		          }
		      }
		  }
		}
	REKOR_PAYLOAD
}

###########################################################################################
# Print Rekor payload
#
# Globals:
#   _arg_payload
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

print_rekor_payload() {
  local rekor_payload_filepath="$(get_rekor_payload_path)"

  log_info "Contents of ${rekor_payload_filepath}:"

  if ! jq_cmd . "${rekor_payload_filepath}"; then
    log_error "Encountered an error when printing the contents of ${rekor_payload_filepath}," \
      "exiting..."
    exit 1
  fi
}

###########################################################################################
# Upload the Rekor payload
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   The status code of the response
###########################################################################################

upload_rekor_payload() {
  local args=(
    "-s"
    "-w"
    "%{http_code}"
    "-o"
    "$(get_rekor_response_path)"
    "-X"
    "POST"
    "-H"
    "Content-Type: application/json"
    "-d"
    "@$(get_rekor_payload_path)"
    "https://rekor.sigstore.dev/api/v1/log/entries"
  )

  if ! curl_cmd "${args[@]}"; then
    log_error "Encountered an error when uploading the Rekor payload," \
      "exiting..."
    exit 1
  fi
}

###########################################################################################
# Extract UUID from the Rekor payload upload response
#
# Globals:
#   None
# Arguments:
#   The response status code, a string
# Returns:
#   The Rekor UUID
###########################################################################################

extract_rekor_response_uuid() {
  local status_code="${1}"
  local rekor_response_path="$(get_rekor_response_path)"
  local response_body="$(cat ${rekor_response_path})"
  local rekor_uuid

  if [[ "${status_code}" == "409" ]]; then
    log_info "Rekor entry already exists, checking for an existing UUID"
    rekor_uuid="$(echo "${response_body}" | jq_cmd -r '.message' | grep_cmd -oE '[a-f0-9]{64,}')"
  elif [[ "${status_code}" == "201" ]]; then
    log_info "Rekor entry created successfully"
    rekor_uuid="$(echo "${response_body}" | jq_cmd -r 'keys[0]')"
  else
    log_error "Unexpected HTTP status code ${status_code}, exiting..."
    exit 1
  fi

  echo "${rekor_uuid}"
}

###########################################################################################
# Export the validated Rekor UUID
#
# Globals:
#   None
# Arguments:
#   The Rekor UUID, a string
# Returns:
#   None
###########################################################################################

export_rekor_uuid() {
  local rekor_uuid="${1}"
  validate_rekor_uuid "${rekor_uuid}"
  log_info "The validated Rekor UUID is ${rekor_uuid}"
  echo "uuid=${rekor_uuid}" >> $GITHUB_OUTPUT
}

###########################################################################################
# The top-level function in the script
#
# Globals:
#   None
# Arguments:
#   Script arguments, an array
# Returns:
#   None
###########################################################################################

main() {
  parse_args "${@}"
  save_payload_to_file
  save_public_key_to_file
  save_rekor_payload
  print_rekor_payload
  local status_code="$(upload_rekor_payload)"
  local rekor_uuid="$(extract_rekor_response_uuid ${status_code})"
  export_rekor_uuid "${rekor_uuid}"
}

###########################################################################################
# Main script
###########################################################################################

main "${@}"
