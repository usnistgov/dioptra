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

SCRIPT_CMDNAME="${0##*/}"
LOGNAME="Init Scripts"
DEFAULT_ARG_OUTPUT="/scripts"

_arg_m4_files=()
_arg_sh_files=()
_arg_output="${DEFAULT_ARG_OUTPUT}"

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
  cat <<HELPMESSAGE
Utility that prepares the deployment initialization scripts.

Usage: ${SCRIPT_CMDNAME} [-o|--output <arg>] [-h|--help] ...
        ...: One or more paths to files with extension '.m4' and '.sh'. Files with the
             extension '.m4' will be processed using argbash while files with the
             extension '.sh' are just copied.
        -o, --output: Target directory for processed scripts (default: '${DEFAULT_ARG_OUTPUT}')
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
# Extract the base name of a path and optionally remove the path extension
#
# Globals:
#   None
# Arguments:
#   Path to a file or directory, a string
#   (Optional) Extension to remove from path, a string
# Outputs:
#   Writes the base name of the provided path, optionally with a file extension removed
# Returns:
#   None
###########################################################################################

extract_basename() {
  local basename_args=("${1}")
  local file_stem

  if [[ ! -z "${2:-}" ]]; then
    basename_args+=("${2}")
  fi

  if ! file_stem="$(basename ${basename_args[@]})"; then
    log_error "Unable to extract file stem from path ${basename_args[0]}, exiting..."
    exit 1
  fi

  echo "${file_stem}"
}

###########################################################################################
# Extract the directory name of a path
#
# Globals:
#   None
# Arguments:
#   Path to a file or directory, a string
# Outputs:
#   Writes the directory name of the provided path
# Returns:
#   None
###########################################################################################

extract_dirname() {
  local filepath="${1}"
  local directory_name

  if ! directory_name="$(dirname ${filepath})"; then
    log_error "Unable to extract directory name from path ${filepath}, exiting..."
    exit 1
  fi

  echo "${directory_name}"
}

###########################################################################################
# Standardize a path
#
# Globals:
#   None
# Arguments:
#   Path to a file or directory, a string
# Outputs:
#   Writes the standardized form of the provided path
# Returns:
#   None
###########################################################################################

standardize_path() {
  local filepath="${1}"
  local directory_name="$(extract_dirname ${filepath})"
  local file_stem="$(extract_basename ${filepath})"
  local standardized_path

  if [[ "${directory_name}" == "/" && "${file_stem}" == "/" ]]; then
    standardized_path="/"
  elif [[ "${directory_name}" == "/" ]]; then
    standardized_path="/${file_stem}"
  elif [[ "${directory_name}" == "." ]]; then
    standardized_path="${file_stem}"
  else
    standardized_path="${directory_name}/${file_stem}"
  fi

  echo "${standardized_path}"
}

###########################################################################################
# Parse the script arguments
#
# Globals:
#   _arg_output
#   _arg_m4_files
#   _arg_sh_files
# Arguments:
#   Script arguments, an array
# Returns:
#   None
###########################################################################################

parse_args() {
  while (({{ '"${#}"' }} > 0)); do
    case "${1}" in
      -h | --help)
        print_help
        exit 0
        ;;
      -o | --output)
        _arg_output="$(standardize_path ${2})"
        shift 2
        ;;
      *.m4)
        _arg_m4_files+=("$(standardize_path ${1})")
        shift 1
        ;;
      *.sh)
        _arg_sh_files+=("$(standardize_path ${1})")
        shift 1
        ;;
      *)
        log_error "Unrecognized argument ${1}, exiting..."
        exit 1
        ;;
    esac
  done
}

###########################################################################################
# Recursively change file access permissions of output directory to 0755
#
# Globals:
#   _arg_output
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

set_chmod_permissions() {
  log_info "Setting access permissions on ${_arg_output} to 0755"

  if ! chmod -R "0755" "${_arg_output}"; then
    log_error "Recursively setting permissions on ${_arg_output} failed, exiting..."
    exit 1
  fi
}

###########################################################################################
# Recursively change file ownership of output directory to root:root
#
# Globals:
#   _arg_output
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

set_chown_permissions() {
  log_info "Setting ownership of ${_arg_output} to root:root"

  if ! chown -R "root:root" "${_arg_output}"; then
    log_error "Recursively setting ownership of ${_arg_output} failed, exiting..."
    exit 1
  fi
}

###########################################################################################
# Copy a source file to a target path
#
# Globals:
#   None
# Arguments:
#   Path to the source file, a string
#   Path to the target file, a string
# Returns:
#   None
###########################################################################################

copy_script() {
  local source_file="${1}"
  local target_file="${2}"

  log_info "Copying ${source_file} to ${target_file}"

  if ! cp "${source_file}" "${target_file}"; then
    log_error "Copying ${source_file} to ${target_file} failed, exiting..."
    exit 1
  fi
}

###########################################################################################
# Render a source file using argbash and save to a target path
#
# Globals:
#   None
# Arguments:
#   Path to the source file, a string
#   Path to the target file, a string
# Returns:
#   None
###########################################################################################

render_bash_script() {
  local source_file="${1}"
  local target_file="${2}"

  log_info "Rendering ${source_file} to ${target_file} using argbash"

  if ! /usr/local/bin/argbash "${source_file}" -o "${target_file}"; then
    log_error "Rendering ${source_file} to ${target_file} using argbash failed," \
      "exiting..."
    exit 1
  fi
}

###########################################################################################
# Process the provided m4 files
#
# Globals:
#   _arg_output
#   _arg_m4_files
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

process_m4_files() {
  local target_filename
  local target_filepath

  for m4_file in "${_arg_m4_files[@]}"; do
    target_filename="$(extract_basename ${m4_file} .m4).sh"

    if [[ "${_arg_output}" == "/" ]]; then
      target_filepath="/${target_filename}"
    else
      target_filepath="${_arg_output}/${target_filename}"
    fi

    render_bash_script "${m4_file}" "${target_filepath}"
  done
}

###########################################################################################
# Process the provided sh files
#
# Globals:
#   _arg_output
#   _arg_sh_files
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

process_sh_files() {
  local target_filename
  local target_filepath

  for sh_file in "${_arg_sh_files[@]}"; do
    target_filename="$(extract_basename ${sh_file})"

    if [[ "${_arg_output}" == "/" ]]; then
      target_filepath="/${target_filename}"
    else
      target_filepath="${_arg_output}/${target_filename}"
    fi

    copy_script "${sh_file}" "${target_filepath}"
  done
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
  process_m4_files
  process_sh_files
  set_chmod_permissions
  set_chown_permissions
}

###########################################################################################
# Main script
###########################################################################################

main "${@}"
