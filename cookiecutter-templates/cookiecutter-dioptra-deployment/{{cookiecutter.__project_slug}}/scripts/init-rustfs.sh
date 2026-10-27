#!/bin/sh
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

set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

{% set rustfs_account_names = ["MLFLOW_TRACKING", "RESTAPI", "WORKER"] -%}
{% set rustfs_policy_names = [
  "mlflow-tracking-readwrite",
] -%}
INIT_REPOS_DIR="/init-repos"
LOGNAME="Init RustFS"
RUSTFS_ENDPOINT_ALIAS="rustfs"
SECRETS_DIR="/secrets"
S3_POLICY_DIR="/s3-policy"

{% for rustfs_account_name in rustfs_account_names -%}
RUSTFS_{{ rustfs_account_name }}_USER=""
RUSTFS_{{ rustfs_account_name }}_PASSWORD=""
RUSTFS_{{ rustfs_account_name }}_POLICIES=""
{% endfor -%}
RUSTFS_ACCESS_KEY=""
RUSTFS_SECRET_KEY=""

# NOTE: Mutable global variable
policies_reduced=""

###########################################################################################
# Print the script help message
#
# Globals:
#   SCRIPT_CMDNAME
# Arguments:
#   Error messages to log, a string
# Returns:
#   None
###########################################################################################

print_help() {
  cat <<-HELPMESSAGE
		Utility that configures the RustFS accounts and policies.

		Usage: init-rustfs.sh [-h|--help]
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
  echo "${LOGNAME}: INFO -" "${@}"
}

###########################################################################################
# Parse the script arguments
#
# Globals:
#   None
# Arguments:
#   Script arguments, an array
# Returns:
#   None
###########################################################################################

parse_args() {
  while [ {{ '"${#}"' }} -gt 0 ]; do
    case "${1}" in
      -h | --help)
        print_help
        exit 0
        ;;
      *)
        log_error "Unrecognized argument ${1}, exiting..."
        exit 1
        ;;
    esac
  done
}

###########################################################################################
# Load account credentials into environment variables
#
# Globals:
{% for rustfs_account_name in rustfs_account_names -%}
#   RUSTFS_{{ rustfs_account_name }}_USER
#   RUSTFS_{{ rustfs_account_name }}_PASSWORD
#   RUSTFS_{{ rustfs_account_name }}_POLICIES
{% endfor -%}
#   RUSTFS_ACCESS_KEY
#   RUSTFS_SECRET_KEY
#   SECRETS_DIR
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

load_account_creds() {
  while IFS="=" read -r key value; do
    case "${key}" in
      {% for rustfs_account_name in rustfs_account_names -%}
      "RUSTFS_{{ rustfs_account_name }}_USER") RUSTFS_{{ rustfs_account_name }}_USER="$value" ;;
      "RUSTFS_{{ rustfs_account_name }}_PASSWORD") RUSTFS_{{ rustfs_account_name }}_PASSWORD="$value" ;;
      "RUSTFS_{{ rustfs_account_name }}_POLICIES") RUSTFS_{{ rustfs_account_name }}_POLICIES="$value" ;;
      {% endfor -%}
      "RUSTFS_ACCESS_KEY") RUSTFS_ACCESS_KEY="$value" ;;
      "RUSTFS_SECRET_KEY") RUSTFS_SECRET_KEY="$value" ;;
    esac
  done < "${SECRETS_DIR}/{{ cookiecutter.__project_slug }}-rustfs-accounts.env"
}

###########################################################################################
# Configure alias for accessing the RustFS endpoint
#
# Globals:
#   RUSTFS_ENDPOINT_ALIAS
#   RUSTFS_ACCESS_KEY
#   RUSTFS_SECRET_KEY
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

set_rustfs_alias() {
  rc alias set \
    "${RUSTFS_ENDPOINT_ALIAS}" \
    "http://{{ cookiecutter.__project_slug }}-rustfs:9000" \
    "${RUSTFS_ACCESS_KEY}" \
    "${RUSTFS_SECRET_KEY}"
}

###########################################################################################
# Create the mlflow-tracking bucket
#
# Globals:
#   RUSTFS_ENDPOINT_ALIAS
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

create_buckets() {
  rc mb --ignore-existing \
    "${RUSTFS_ENDPOINT_ALIAS}/mlflow-tracking"
}

###########################################################################################
# Create the RustFS accounts
#
# Globals:
#   RUSTFS_ENDPOINT_ALIAS
{% for rustfs_account_name in rustfs_account_names -%}
#   RUSTFS_{{ rustfs_account_name }}_USER
#   RUSTFS_{{ rustfs_account_name }}_PASSWORD
{% endfor -%}
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

create_rustfs_accounts() {
{%- for rustfs_account_name in rustfs_account_names %}
  rc admin user add \
    "${RUSTFS_ENDPOINT_ALIAS}" "{{ '${RUSTFS_' ~ rustfs_account_name ~ '_USER}' }}" \
    "{{ '${RUSTFS_' ~ rustfs_account_name ~ '_PASSWORD}' }}"
{% endfor -%}
}

###########################################################################################
# Create RustFS access policies
#
# Globals:
#   RUSTFS_ENDPOINT_ALIAS
#   S3_POLICY_DIR
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

create_rustfs_policies() {
{%- for policy_name in rustfs_policy_names %}
  rc admin policy create \
    "${RUSTFS_ENDPOINT_ALIAS}" "{{ policy_name }}" "${S3_POLICY_DIR}/{{ policy_name }}-policy.json"
{% endfor -%}
}

###########################################################################################
# Remove elements from a comma-separated list
#
# Globals:
#   LOGNAME
# Arguments:
#   Input list, a comma-separated string
#   Elements to match and delete, a comma-separated string
# Returns:
#   List with elements removed, a comma-separated string
###########################################################################################

remove_elements_from_comma_delimited() {
  local input_list="${1}"
  local elements_to_delete="${2}"
  jq -nr --arg input "$input_list" --arg delete "$elements_to_delete" '
    ($input | split(",") | map(select(length > 0)) | unique) -
    ($delete | split(",")) | join(",")
  '
}

###########################################################################################
# Set the policies to attach in global policies_reduced after deduplicating repeat policies
#
# Globals:
#   LOGNAME
#   policies_reduced
# Arguments:
#   The current policy to user mappings, a JSON string
#   The target policies for a user
#   The target user
# Returns:
#   None
###########################################################################################

remove_repeat_policies() {
  local mappings=$1
  local policies=$2
  local user=$3
  local attached_policies

  attached_policies=$(printf '%s\n' "$mappings" | jq -r --arg user "$user" '
    [.data.user_mappings[] | select(.user == $user) | .policies[]] | join(",")
  ')
  policies_reduced=$(remove_elements_from_comma_delimited "$policies" "$attached_policies")
  if [ -n "${policies_reduced}" ]; then
    # rc replaces the policy list, so retain existing attachments when adding policies.
    policies_reduced=$(remove_elements_from_comma_delimited "${attached_policies},${policies_reduced}" "")
  fi
}

###########################################################################################
# Attach RustFS policies to user accounts
#
# Globals:
#   RUSTFS_ENDPOINT_ALIAS
{% for rustfs_account_name in rustfs_account_names -%}
#   RUSTFS_{{ rustfs_account_name }}_USER
#   RUSTFS_{{ rustfs_account_name }}_POLICIES
{% endfor -%}
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

attach_rustfs_policies() {
  local attached_policies

{% for rustfs_account_name in rustfs_account_names %}
  attached_policies=$(rc --json admin policy entities "${RUSTFS_ENDPOINT_ALIAS}" \
    --user="{{ '${RUSTFS_' ~ rustfs_account_name ~ '_USER}' }}")
  remove_repeat_policies "${attached_policies}" \
    "{{ '${RUSTFS_' ~ rustfs_account_name ~ '_POLICIES}' }}" "{{ '${RUSTFS_' ~ rustfs_account_name ~ '_USER}' }}"

  if [ -n "${policies_reduced}" ]; then
    rc admin policy attach \
      "${RUSTFS_ENDPOINT_ALIAS}" \
      "${policies_reduced}" \
      --user="{{ '${RUSTFS_' ~ rustfs_account_name ~ '_USER}' }}"
  fi
{% endfor -%}
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
  parse_args "${@}"
  load_account_creds
  set_rustfs_alias
  create_buckets
  create_rustfs_accounts
  create_rustfs_policies
  attach_rustfs_policies
}

###########################################################################################
# Main script
###########################################################################################

main "${@}"
