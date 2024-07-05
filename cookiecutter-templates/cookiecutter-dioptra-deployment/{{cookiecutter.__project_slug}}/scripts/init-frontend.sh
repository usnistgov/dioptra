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
LOGNAME="Init Frontend"
DIOPTRA_REPO_DIR="/repo/dioptra"
BUILD_DIR="/build"
DEFAULT_ARG_OUTPUT="/frontend"

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
Utility that compiles the Vue.js frontend for serving.

Usage: ${SCRIPT_CMDNAME} [-o|--output <arg>] [-h|--help]
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
# Recursively remove all files within a directory
#
# Globals:
#   None
# Arguments:
#   Directory to be cleared, a path
# Returns:
#   None
###########################################################################################

clear_dir() {
  local dir_path="${1}"

  log_info "Clearing the directory ${dir_path}"

  if ! rm -vrf ${dir_path}; then
    log_error "Clearing the directory ${dir_path} failed"
    exit 1
  fi
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
      *)
        log_error "Unrecognized argument ${1}, exiting..."
        exit 1
        ;;
    esac
  done
}

###########################################################################################
# Recursively change access permissions of output directory to 0755 (dirs) and 0644 (files)
#
# Globals:
#   _arg_output
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

set_chmod_permissions() {
  log_info "Setting directory permissions under ${_arg_output} to 0755"

  if ! (find "${_arg_output}" -type d -print0 | xargs -0 chmod "0755"); then
    log_error "Recursively changing directory permissions under ${_arg_output} failed"
    exit 1
  fi

  log_info "Setting file permissions under ${_arg_output} to 0644"

  if ! (find "${_arg_output}" -type f -print0 | xargs -0 chmod "0644"); then
    log_error "Recursively changing file permissions under ${_arg_output} failed"
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
# Copy frontend source files into the build directory
#
# Globals:
#   BUILD_DIR
#   DIOPTRA_REPO_DIR
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

prepare_build_dir() {
  local src_frontend_dir="${DIOPTRA_REPO_DIR}/src/frontend"
  local src_names=(
    "src"
    "public"
    "index.html"
    "package.json"
    "tsconfig.json"
    "tsconfig.app.json"
    "tsconfig.node.json"
    "vite.config.ts"
  )

  log_info "Creating the build directory ${BUILD_DIR}"

  if ! mkdir -p "${BUILD_DIR}"; then
    log_error "Creating the directory ${BUILD_DIR} failed, exiting..."
    exit 1
  fi

  for src_name in "${src_names[@]}"; do
    log_info "Copying ${src_frontend_dir}/${src_name} into ${BUILD_DIR}/${src_name}"
    if ! cp -r ${src_frontend_dir}/${src_name} ${BUILD_DIR}/${src_name}; then
      log_error "Copying ${src_frontend_dir}/${src_name} into ${BUILD_DIR}/${src_name}" \
        "failed, exiting..."
      exit 1
    fi
  done
}

###########################################################################################
# Copy the compiled dist contents to the target directory
#
# Globals:
#   BUILD_DIR
#   _arg_output
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

copy_dist_to_output() {
  local dist_dir="${BUILD_DIR}/dist"

  clear_dir "${_arg_output}/*"

  log_info "Copying contents of ${dist_dir} into ${_arg_output}"

  if ! cp -r ${dist_dir}/* ${_arg_output}/.; then
    log_error "Copying contents of ${dist_dir} into ${_arg_output} failed, exiting..."
    exit 1
  fi
}

###########################################################################################
# Render a source file using argbash and save to a target path
#
# Globals:
#   BUILD_DIR
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

compile_vue_js_frontend() {
  cd "${BUILD_DIR}"

  log_info "Installing node packages using npm install"

  if ! npm install; then
    log_error "Installing node modules using npm install failed, exiting..."
    exit 1
  fi

  log_info "Compiling Vue.js files using npm run build"

  if ! npm run build; then
    log_error "Compiling of frontend Vue.js files using npm run build failed, exiting..."
    exit 1
  fi
}

###########################################################################################
# The top-level function in the script
#
# Globals:
#   _arg_output
# Arguments:
#   Script arguments, an array
# Returns:
#   None
###########################################################################################

main() {
  parse_args "${@}"
  prepare_build_dir
  compile_vue_js_frontend
  copy_dist_to_output
  set_chmod_permissions
  set_chown_permissions
}

###########################################################################################
# Main script
###########################################################################################

main "${@}"
