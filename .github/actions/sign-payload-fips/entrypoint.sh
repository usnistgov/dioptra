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

LOGNAME="OpenSSL FIPS Entrypoint"

PAYLOAD_FILENAME="payload.json"
PUBLIC_KEY_FILENAME="public.pub"
PRIVATE_KEY_FILENAME="private.pem"
SIGNATURE_FILENAME="payload.sig"

TEMP_DIR="$(mktemp -d)"

_arg_payload=""
_arg_private_key=""
_arg_public_key=""

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
		Sign and verify payloads using FIPS-compliant OpenSSL.

		Usage: entrypoint.sh [--payload <arg>] [--private-key <arg>]
		                     [--public-key <arg>] [-h|--help]
		        --payload: The payload to be signed and verified (required)
		        --private-key: The private key to use when signing a payload (required)
		        --public-key: The public key to use when verifying a payload (required)
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
# Validate private key variable is not empty
#
# Globals:
#   _arg_private_key
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_private_key_provided() {
  if [[ -z "${_arg_private_key}" ]]; then
    log_error "A private key was not provided, exiting..."
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
# Get the path to the private key file
#
# Globals:
#   PRIVATE_KEY_FILENAME
#   TEMP_DIR
# Arguments:
#   None
# Returns:
#   The full path for the private key file, a string
###########################################################################################

get_private_key_path() {
  # Remove a trailing slash if present
  local dir_prefix="${TEMP_DIR%/}"

  # Remove a leading slash if present
  local filename="${PRIVATE_KEY_FILENAME#/}"

  # Return full path to the private key file
  echo "${dir_prefix}/${filename}"
}

###########################################################################################
# Get the path to signature file
#
# Globals:
#   SIGNATURE_FILENAME
#   TEMP_DIR
# Arguments:
#   None
# Returns:
#   The full path for the signature file, a string
###########################################################################################

get_signature_path() {
  # Remove a trailing slash if present
  local dir_prefix="${TEMP_DIR%/}"

  # Remove a leading slash if present
  local filename="${SIGNATURE_FILENAME#/}"

  # Return full path to the signature file
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
# Wrapper for invoking openssl
#
# Globals:
#   None
# Arguments:
#   Positional arguments, one or more strings
# Returns:
#   None
###########################################################################################

openssl_cmd() {
  if ! openssl "${@}"; then
    log_error "Encountered an error when executing openssl, exiting..."
    exit 1
  fi
}

###########################################################################################
# Wrapper for invoking shred
#
# Globals:
#   None
# Arguments:
#   Positional arguments, one or more strings
# Returns:
#   None
###########################################################################################

shred_cmd() {
  if ! shred "${@}"; then
    log_error "Encountered an error when executing shred, exiting..."
    exit 1
  fi
}

###########################################################################################
# Parse the script arguments
#
# Globals:
#   _arg_payload
#   _arg_private_key
#   _arg_public_key
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
      --private-key)
        _arg_private_key="${2}"
        shift 2
        ;;
      --public-key)
        _arg_public_key="${2}"
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
# Print OpenSSL version
#
# Globals:
#   _arg_payload
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

print_openssl_version() {
  log_info "$(openssl_cmd version)"
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

  if ! echo "${_arg_payload}" > "${payload_path}"; then
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
# Save private key to a file
#
# Globals:
#   _arg_private_key
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

save_private_key_to_file() {
  validate_private_key_provided

  local private_key_path="$(get_private_key_path)"

  if ! echo "${_arg_private_key}" > "${private_key_path}"; then
    log_error "Encountered an error when saving the private key to ${private_key_path}," \
      "exiting..."
    exit 1
  fi

  if ! chmod 0400 "${private_key_path}"; then
    log_error "Encountered an error when changing the file permissions on the private " \
      "key file ${private_key_path}, exiting..."
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
# Export base64-encoded signature file
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

export_signature_file() {
  local signature_path="$(get_signature_path)"
  local signature_contents_b64="$(base64_encode ${signature_path})"
  log_info "Exporting the base64-encoded signature ${signature_contents_b64}"
  echo "signature=${signature_contents_b64}" >> $GITHUB_OUTPUT
}

###########################################################################################
# Shred private key
#
# Globals:
#   _arg_private_key
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

shred_private_key() {
  local private_key_path="$(get_private_key_path)"

  if ! shred_cmd -u "${private_key_path}"; then
    log_error "Encountered an error when destroying the private key ${private_key_path}," \
      "exiting..."
    exit 1
  fi
}

###########################################################################################
# Sign a payload
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

sign_payload() {
  local args=(
    "dgst"
    "-sha256"
    "-sign"
    "$(get_private_key_path)"
    "-out"
    "$(get_signature_path)"
    "$(get_payload_path)"
  )

  if ! openssl_cmd "${args[@]}"; then
    log_error "Encountered an error when signing the payload," \
      "exiting..."
    exit 1
  fi
}

###########################################################################################
# Verify a payload
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

verify_payload() {
  local args=(
    "dgst"
    "-sha256"
    "-verify"
    "$(get_public_key_path)"
    "-signature"
    "$(get_signature_path)"
    "$(get_payload_path)"
  )

  if ! openssl_cmd "${args[@]}"; then
    log_error "Encountered an error when verifying the payload," \
      "exiting..."
    exit 1
  fi

  log_info "Payload signature verification successful!"
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
  save_private_key_to_file
  print_openssl_version
  sign_payload
  shred_private_key
  verify_payload
  export_signature_file
}

###########################################################################################
# Main script
###########################################################################################

main "${@}"
