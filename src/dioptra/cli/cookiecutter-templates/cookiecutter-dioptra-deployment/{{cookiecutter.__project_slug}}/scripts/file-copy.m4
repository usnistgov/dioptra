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
# ARG_POSITIONAL_INF([srcdest], [Source destination pairs to use for copying], [2])
# ARG_OPTIONAL_BOOLEAN([recursive],[r],[Recursive copying])
# ARG_OPTIONAL_SINGLE([chmod],[],[File access permission setting],[0644])
# ARG_OPTIONAL_SINGLE([chown],[],[File ownership setting],[39000:100])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Container Initialization - Copy Files\n])"
# ARGBASH_GO()

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

readonly src_dest_pairs_length={{ '"${#_arg_srcdest[@]}"' }}
readonly chmod_setting="${_arg_chmod}"
readonly chown_setting="${_arg_chown}"
readonly recursive="${_arg_recursive}"
readonly logname="File Copy"

###########################################################################################
# Print an error log message to stderr
#
# Globals:
#   logname
# Arguments:
#   Error messages to log, one or more strings
# Returns:
#   None
###########################################################################################

log_error() {
  echo "${logname}: ERROR -" "${@}" 1>&2
}

###########################################################################################
# Print an informational log message to stdout
#
# Globals:
#   logname
# Arguments:
#   Info messages to log, one or more strings
# Returns:
#   None
###########################################################################################

log_info() {
  echo "${logname}: INFO -" "${@}"
}

###########################################################################################
# Copy file operation
#
# Globals:
#   recursive
#   src_dest_pairs_length
#   _arg_srcdest
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

copy_files() {
  local idx=0
  local idx_two=0
  local src_filepath=""
  local dest_filepath=""
  local extra_opts=()

  if [[ ${recursive} == on ]]; then
    extra_opts+=("-r")
  fi

  for ((idx = 0; idx < ${src_dest_pairs_length}; idx += 2)); do
    idx_two=$((${idx} + 1))
    src_filepath="${_arg_srcdest[idx]}"
    dest_filepath="${_arg_srcdest[idx_two]}"

    if [[ "${recursive}" == "on" ]]; then
      log_info "Recursively copy ${src_filepath} to ${dest_filepath}"
    else
      log_info "Copy ${src_filepath} to ${dest_filepath}"
    fi

    if ! cp "${extra_opts[@]}" "${src_filepath}" "${dest_filepath}"; then
      log_error "Copying ${src_filepath} to ${dest_filepath} failed"
      exit 1
    fi
  done
}

###########################################################################################
# Change file access permissions
#
# Globals:
#   chmod_setting
#   recursive
#   src_dest_pairs_length
#   _arg_srcdest
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

chmod_files() {
  local idx=0
  local idx_two=0
  local dest_filepath=""

  for ((idx = 0; idx < ${src_dest_pairs_length}; idx += 2)); do
    idx_two=$((${idx} + 1))
    dest_filepath="${_arg_srcdest[idx_two]}"

    if [[ "${recursive}" == "on" ]]; then
      log_info "Recursively change file access permissions under ${dest_filepath} to" \
        "${chmod_setting}"
    else
      log_info "Change file access permission of ${dest_filepath} to ${chmod_setting}"
    fi

    if [[ "${recursive}" == "on" ]]; then
      if ! find "${dest_filepath}" -type f -print0 | xargs -0 chmod "${chmod_setting}"; then
        log_error "Setting file access permissions in ${dest_filepath} folder to" \
          "${chmod_setting} failed"
        exit 1
      fi
    else
      if ! chmod "${chmod_setting}" "${dest_filepath}"; then
        log_error "Setting file access permission of ${dest_filepath} to" \
          "${chmod_setting} failed"
        exit 1
      fi
    fi
  done
}

###########################################################################################
# Change file ownership
#
# Globals:
#   chown_setting
#   src_dest_pairs_length
#   _arg_srcdest
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

chown_files() {
  local idx=0
  local idx_two=0
  local dest_filepath=""
  local extra_opts=()

  if [[ "${recursive}" == "on" ]]; then
    extra_opts+=("-R")
  fi

  for ((idx = 0; idx < ${src_dest_pairs_length}; idx += 2)); do
    idx_two=$((${idx} + 1))
    dest_filepath="${_arg_srcdest[idx_two]}"

    if [[ "${recursive}" == "on" ]]; then
      log_info "Recursively change ownership of ${dest_filepath} to ${chown_setting}"
    else
      log_info "Change ownership of ${dest_filepath} to ${chown_setting}"
    fi

    if ! chown "${extra_opts[@]}" "${chown_setting}" "${dest_filepath}"; then
      log_error "Changing ownership of ${dest_filepath} to ${chown_setting} failed"
      exit 1
    fi
  done
}

###########################################################################################
# Main script
###########################################################################################

copy_files
chown_files
chmod_files
# ] <-- needed because of Argbash
