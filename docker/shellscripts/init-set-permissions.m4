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
# ARG_POSITIONAL_INF([dest],[List of filepaths],[1])
# ARG_OPTIONAL_BOOLEAN([recursive],[r],[Recursive copying, <dest> must be a list of directories])
# ARG_OPTIONAL_SINGLE([dir-chmod],[],[Directory access permission setting],[0755])
# ARG_OPTIONAL_SINGLE([file-chmod],[],[File access permission setting],[0644])
# ARG_OPTIONAL_SINGLE([chown],[],[File ownership setting],[39000:100])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Container Initialization - Set Permissions\n])"
# ARGBASH_GO()

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

readonly dir_chmod_setting="${_arg_dir_chmod}"
readonly file_chmod_setting="${_arg_file_chmod}"
readonly chown_setting="${_arg_chown}"
readonly recursive="${_arg_recursive}"
readonly logname="Container Init: Set Permissions"

###########################################################################################
# Validate that only directories were passed to <dest> if using --recursive
#
# Globals:
#   logname
#   recursive
#   _arg_dest
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_directories_only_when_recursive() {
  local error_count=0

  for filepath in ${_arg_dest[@]}; do
    if [[ ! -d ${filepath} ]]; then
      echo "${logname}: ERROR - ${filepath} is not a directory (required when using" \
        "--recursive)." 1>&2
      ((error_count += 1))
    fi
  done

  if ((${error_count} > 0)); then
    echo "${logname}: ERROR - Only directories can be passed to <dest> when using"\
      "--recursive. Please review your filepath list and try again." 1>&2
    exit 1
  fi
}

###########################################################################################
# Change access permissions for a single directory
#
# Globals:
#   logname
#   dir_chmod_setting
# Arguments:
#   Individual directory, a path.
# Returns:
#   None
###########################################################################################

chmod_directory() {
  local filepath="$1"

  echo "${logname}: INFO - Change directory access permission of ${filepath} to" \
    "${dir_chmod_setting}"

  if ! (chmod ${dir_chmod_setting} ${filepath}); then
    echo "${logname}: ERROR - Changing directory permissions of ${filepath}" \
      "failed." 1>&2
    exit 1
  fi
}

###########################################################################################
# Change access permissions for a single file
#
# Globals:
#   logname
#   file_chmod_setting
# Arguments:
#   Individual file, a path.
# Returns:
#   None
###########################################################################################

chmod_file() {
  local filepath="$1"

  echo "${logname}: INFO - Change file access permission of ${filepath} to" \
    "${file_chmod_setting}"

  if ! (chmod ${file_chmod_setting} ${filepath}); then
    echo "${logname}: ERROR - Changing directory permissions of ${filepath}" \
      "failed." 1>&2
    exit 1
  fi
}

###########################################################################################
# Change access permissions for a single filepath
#
# Globals:
#   logname
# Arguments:
#   File or directory, a path.
# Returns:
#   None
###########################################################################################

chmod_filepath() {
  local filepath="$1"

  if [[ -f ${filepath} ]]; then
    chmod_file ${filepath}
  elif [[ -d ${filepath} ]]; then
    chmod_directory ${filepath}
  else
    echo "${logname}: ERROR - Unable to determine if ${filepath} is a file or" \
      "a directory." 1>&2
    exit 1
  fi
}

###########################################################################################
# Recursively change directory access permissions under a parent directory
#
# Globals:
#   logname
#   dir_chmod_setting
# Arguments:
#   Parent directory, a path.
# Returns:
#   None
###########################################################################################

recursive_chmod_directories() {
  local directory="$1"

  echo "${logname}: INFO - Recursively change directory access permissions under" \
    "${directory} to ${dir_chmod_setting}"

  if ! (find ${directory} -type d -print0 | xargs -0 chmod ${dir_chmod_setting}); then
    echo "${logname}: ERROR - Recursively changing directory permissions under" \
      "${directory} failed." 1>&2
    exit 1
  fi
}

###########################################################################################
# Recursively change file access permissions under a parent directory
#
# Globals:
#   logname
#   file_chmod_setting
# Arguments:
#   Parent directory, a path.
# Returns:
#   None
###########################################################################################

recursive_chmod_files() {
  local directory="$1"

  echo "${logname}: INFO - Recursively change directory access permissions under" \
    "${directory} to ${dir_chmod_setting}"

  if ! (find ${directory} -type f -print0 | xargs -0 chmod ${file_chmod_setting}); then
    echo "${logname}: ERROR - Recursively changing file permissions under ${directory}" \
      "failed." 1>&2
    exit 1
  fi
}

###########################################################################################
# Change ownership of a file or directory
#
# Globals:
#   logname
# Arguments:
#   File or directory, a path.
# Returns:
#   None
###########################################################################################

chown_filepath() {
  local filepath="$1"

  echo "${logname}: INFO - Change ownership of ${filepath} to ${chown_setting}"

  if ! (chown ${chown_setting} ${filepath}); then
    echo "${logname}: ERROR - Changing ownership of ${filepath} failed." 1>&2
    exit 1
  fi
}

###########################################################################################
# Recursively change ownership under a parent directory
#
# Globals:
#   logname
#   chown_setting
# Arguments:
#   Parent directory, a path.
# Returns:
#   None
###########################################################################################

recursive_chown_directory() {
  local directory="$1"

  echo "${logname}: INFO - Recursively change ownership of ${directory} to" \
    "${chown_setting}"

  if ! (chown -R ${chown_setting} ${directory}); then
    echo "${logname}: ERROR - Recursively changing ownership of ${directory} failed." 1>&2
    exit 1
  fi
}

###########################################################################################
# The top-level function in the script
#
# Globals:
#   logname
#   recursive
#   _arg_dest
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

main() {
  case "${recursive}" in
    on)
      validate_directories_only_when_recursive
      for directory in ${_arg_dest[@]}; do
        recursive_chmod_directories ${directory}
        recursive_chmod_files ${directory}
        recursive_chown_directory ${directory}
      done
      ;;
    off)
      for filepath in ${_arg_dest[@]}; do
        chmod_filepath ${filepath}
        chown_filepath ${filepath}
      done
      ;;
    *)
      echo "${logname}: ERROR - Unexcepted value of recursive '${recursive}'." 1>&2
      exit 1
      ;;
  esac
}

###########################################################################################
# Main script
###########################################################################################

main
# ] <-- needed because of Argbash
