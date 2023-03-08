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
# ARG_POSITIONAL_SINGLE([source-dir],[Path to source directory],[])
# ARG_POSITIONAL_SINGLE([dest-dir],[Destination directory for files matched with <glob-pattern>],[])
# ARG_POSITIONAL_SINGLE([glob-pattern],[Globbing pattern for matching files in <source-dir>],[])
# ARG_OPTIONAL_SINGLE([chmod],[],[File access permission setting],[0644])
# ARG_OPTIONAL_SINGLE([chown],[],[File ownership setting],[39000:100])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Utility for copying files matching a globbing pattern into a target folder with proper ownership and access permissions\n])
# ARGBASH_GO()

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

LOGNAME="Globbed Copy"

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
# Count the number of globbed files
#
# Globals:
#   _arg_glob_pattern
#   _arg_source_dir
# Outputs:
#   Writes the number of globbed files
# Returns:
#   None
###########################################################################################

count_globbed_files() {
  local -i num_files="$(
    find ${_arg_source_dir} -maxdepth 1 -name ${_arg_glob_pattern} -print |
      wc -l 2>/dev/null ||
      echo '-1'
  )"

  if ((num_files < 0)); then
    log_error "Counting of files in ${_arg_source_dir} failed"
    exit 1
  fi

  echo "${num_files}"
}

###########################################################################################
# Exit early if no files matched by globbing pattern
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

exit_early_if_no_files_matched() {
  local num_files="$(count_globbed_files)"

  if ((num_files == 0)); then
    log_info "No files matched by globbing pattern, skipping..."
    exit 0
  fi
}

###########################################################################################
# Copy globbed files into the target folder
#
# Globals:
#   _arg_dest_dir
#   _arg_glob_pattern
#   _arg_source_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

copy_globbed_files() {
  log_info "Copy files in ${_arg_source_dir} that match glob pattern" \
    "${_arg_glob_pattern} to folder ${_arg_dest_dir}"

  if ! find "${_arg_source_dir}" -maxdepth 1 -name "${_arg_glob_pattern}" -print0 |
    xargs -r -0 -I "{}" cp -v "{}" "${_arg_dest_dir}"; then
    log_error "Copying of globbed files failed"
    exit 1
  fi
}

###########################################################################################
# Set the access permissions
#
# Globals:
#   _arg_dest_dir
#   _arg_chmod
#   _arg_glob_pattern
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

set_access_permissions() {
  log_info "Change access permissions of copied files to ${_arg_chmod}"

  if ! find "${_arg_dest_dir}" -maxdepth 1 -name "${_arg_glob_pattern}" -type f -print0 |
    xargs -0 chmod "${_arg_chmod}"; then
    log_error "Setting access permissions of copied files failed"
    exit 1
  fi
}

###########################################################################################
# Set ownership
#
# Globals:
#   _arg_chown
#   _arg_dest_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

set_ownership() {
  log_info "Recursively change file ownership of destination folder ${_arg_dest_dir} to" \
    "${_arg_chown}"

  if ! chown -R "${_arg_chown}" "${_arg_dest_dir}"; then
    log_error "Recursively changing file ownership of destination folder failed"
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
  exit_early_if_no_files_matched
  copy_globbed_files
  set_access_permissions
  set_ownership
}

###########################################################################################
# Main script
###########################################################################################

main
# ] <-- needed because of Argbash
