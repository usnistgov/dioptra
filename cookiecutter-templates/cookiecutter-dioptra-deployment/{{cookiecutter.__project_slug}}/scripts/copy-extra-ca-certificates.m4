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
# ARG_OPTIONAL_SINGLE([ca-directory],[],[The source directory for extra CAs],[/ca-certificates])
# ARG_OPTIONAL_SINGLE([output],[],[Target directory for extra CAs, the target directory will be inferred if not provided],[])
# ARG_OPTIONAL_SINGLE([chmod],[],[File access permission setting],[0644])
# ARG_OPTIONAL_SINGLE([chown],[],[File ownership setting],[root:root])
# ARG_OPTIONAL_BOOLEAN([update],[],[Update the system-wide CA certificates bundle])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Utility for copying additional certificate authorities (PEM format) into a RHEL-like or Debian-like certificate store\n])
# ARGBASH_GO()

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

LOGNAME="Copy Extra CA Certificates"

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
# Look-up the name of the current operating system
#
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Writes the name of the current operating system
# Returns:
#   None
###########################################################################################

get_os_name() {
  local os_name="$(uname 2>/dev/null || echo 'Unknown')"

  echo "${os_name}"
}

###########################################################################################
# Look-up the name of the current Linux distro
#
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Writes the name of the current Linux distro
# Returns:
#   None
###########################################################################################

get_distro_name() {
  local distro="$(. /etc/os-release && echo ${ID} || echo 'Unknown')"

  echo "${distro}"
}

###########################################################################################
# Look-up the folder to use to store extra CA certificates
#
# Globals:
#   _arg_output
# Arguments:
#   Name of the current Linux distro, a string
# Outputs:
#   Writes the path to the folder to use for storing extra CA certificates
# Returns:
#   None
###########################################################################################

get_extra_ca_certificates_dir() {
  local output
  local distro="${1}"

  if [[ ! -z "${_arg_output}" ]]; then
    output="${_arg_output}"
  elif [[ "${distro}" == "ubuntu" || "${distro}" == "debian" ]]; then
    output="/usr/local/share/ca-certificates"
  elif [[ "${distro}" == "rhel" || "${distro}" == "centos" || "${distro}" == "rocky" ]]; then
    output="/etc/pki/ca-trust/source/anchors"
  else
    log_error "Unable to infer the folder that ${distro} uses to store extra CA" \
      "certificates"
    exit 1
  fi

  echo "${output}"
}

###########################################################################################
# Count the number of files ending in crt in extra CA certificates folder
#
# Globals:
#   _arg_ca_directory
# Outputs:
#   Writes the number of crt files in the extra CA certificates folder
# Returns:
#   None
###########################################################################################

count_crt_files() {
  local -i num_files="$(
    find ${_arg_ca_directory} -name '*.crt' -print | wc -l 2>/dev/null || echo '-1'
  )"

  if ((num_files < 0)); then
    log_error "Counting of extra CA certificates in ${_arg_ca_directory} failed"
    exit 1
  fi

  echo "${num_files}"
}

###########################################################################################
# Exit early if no extra CA certificates are found
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

exit_early_if_no_extra_ca_certificates_found() {
  local num_files="$(count_crt_files)"

  if ((num_files == 0)); then
    log_info "No extra CA files provided, will use default CA bundle"
    exit 0
  fi
}

###########################################################################################
# Copy extra CA certificates into the target folder
#
# Globals:
#   _arg_ca_directory
# Arguments:
#   Folder to use for storing extra CA certificates, a path
# Returns:
#   None
###########################################################################################

copy_extra_ca_certificates() {
  local output="${1}"

  log_info "Copy extra CA certificates from ${_arg_ca_directory} to ${output}"

  if ! find "${_arg_ca_directory}" -name "*.crt" -print0 |
    xargs -r -0 -I "{}" cp -v "{}" "${output}"; then
    log_error "Copying of extra CA certificates failed"
    exit 1
  fi
}

###########################################################################################
# Set the access permissions of extra CA certificates
#
# Globals:
#   _arg_chmod
# Arguments:
#   Folder to use for storing extra CA certificates, a path
# Returns:
#   None
###########################################################################################

set_access_permissions() {
  local output="${1}"

  log_info "Change access permissions of extra CA certificates to ${_arg_chmod}"

  if ! find "${output}" -name "*.crt" -type f -print0 |
    xargs -0 chmod "${_arg_chmod}"; then
    log_error "Setting access permissions of extra CA certificates failed"
    exit 1
  fi
}

###########################################################################################
# Set the ownership of extra CA certificates
#
# Globals:
#   _arg_chown
# Arguments:
#   Folder to use for storing extra CA certificates, a path
# Returns:
#   None
###########################################################################################

set_ownership() {
  local output="${1}"

  log_info "Change ownership of extra CA certificates in ${output} to ${_arg_chown}"

  if ! find "${output}" -name "*.crt" -type f -print0 |
    xargs -0 chown "${_arg_chown}"; then
    log_error "Changing file ownership of CA certificates failed"
    exit 1
  fi
}

###########################################################################################
# Update the CA certificates bundle
#
# Globals:
#   None
# Arguments:
#   Name of the current Linux distro, a string
# Returns:
#   None
###########################################################################################

update_ca_certificates_bundle() {
  local distro="${1}"

  log_info "Update the CA certificates bundle"

  if [[ "${distro}" == "ubuntu" || "${distro}" == "debian" ]]; then
    if ! /usr/sbin/update-ca-certificates; then
      log_error "Failed to update the CA certificates bundle"
      exit 1
    fi
  elif [[ "${distro}" == "rhel" || "${distro}" == "centos" || "${distro}" == "rocky" ]]; then
    if ! /bin/update-ca-trust; then
      log_error "Failed to update the CA certificates bundle"
      exit 1
    fi
  else
    log_error "The distro ${distro} is not supported"
    exit 1
  fi
}

###########################################################################################
# Validate that the script is running in a Linux environment
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_os_is_linux() {
  local os_name="$(get_os_name)"

  if [[ "${os_name}" != "Linux" ]]; then
    log_error "This script is only compatible with Linux"
    exit 1
  fi
}

###########################################################################################
# Validate that the script is able to run in the current Linux distro
#
# Globals:
#   _arg_output
#   _arg_update
# Arguments:
#   Name of the current Linux distro, a string
# Returns:
#   None
###########################################################################################

validate_script_can_run_in_current_distro() {
  local distro="${1}"

  if [[ ! ("${distro}" == "ubuntu" ||
    "${distro}" == "debian" ||
    "${distro}" == "rhel" ||
    "${distro}" == "centos" ||
    "${distro}" == "rocky") ]]; then
    if [[ -z "${_arg_output}" ]]; then
      log_error "This script cannot infer the location of the extra CA certificates" \
        "folder for distro ${distro}"
      exit 1
    elif [[ "${_arg_update}" == "on" ]]; then
      log_error "This script cannot update the CA certificates bundle for distro " \
        "${distro}"
      exit 1
    fi
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
  validate_os_is_linux

  local distro="$(get_distro_name)"

  validate_script_can_run_in_current_distro "${distro}"
  exit_early_if_no_extra_ca_certificates_found

  local output="$(get_extra_ca_certificates_dir ${distro})"

  copy_extra_ca_certificates "${output}"
  set_access_permissions "${output}"
  set_ownership "${output}"

  if [[ "${_arg_update}" == "on" ]]; then
    update_ca_certificates_bundle "${distro}"
  fi
}

###########################################################################################
# Main script
###########################################################################################

main
# ] <-- needed because of Argbash
