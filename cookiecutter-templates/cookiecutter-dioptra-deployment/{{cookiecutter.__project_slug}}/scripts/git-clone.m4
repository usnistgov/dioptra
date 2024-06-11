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
# ARG_POSITIONAL_SINGLE([repo-url],[Git repo URL to clone])
# ARG_POSITIONAL_SINGLE([dest-dir],[Cloning destination folder])
# ARG_OPTIONAL_SINGLE([dir-chmod],[],[Directory access permission setting],[0755])
# ARG_OPTIONAL_SINGLE([file-chmod],[],[File access permission setting],[0644])
# ARG_OPTIONAL_SINGLE([chown],[],[File ownership setting],[39000:100])
# ARG_OPTIONAL_SINGLE([branch],[b],[Clone and checkout a specific branch],[])
# ARG_OPTIONAL_BOOLEAN([single-branch],[],[Only clone the history of the target branch])
# ARG_OPTIONAL_BOOLEAN([force],[f],[Remove target directory if exists and reclone])
# ARG_USE_ENV([GIT_ACCESS_USER],[],[Username to use when cloning the repository])
# ARG_USE_ENV([GIT_ACCESS_TOKEN],[],[Personal access token to use when cloning the repository])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Container Initialization - Git Clone\n])"
# ARGBASH_GO()

# [ <-- needed because of Argbash
shopt -s extglob dotglob nullglob
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

readonly git_user="${GIT_ACCESS_USER:-}"
readonly git_pat="${GIT_ACCESS_TOKEN:-}"
readonly repo_url="${_arg_repo_url}"
readonly dest_dir="${_arg_dest_dir}"
readonly dir_chmod_setting="${_arg_dir_chmod}"
readonly file_chmod_setting="${_arg_file_chmod}"
readonly chown_setting="${_arg_chown}"
readonly branch="${_arg_branch:-}"
readonly single_branch="${_arg_single_branch}"
readonly force="${_arg_force}"
readonly logname="Git Clone"

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
# Print a warning log message to stderr
#
# Globals:
#   logname
# Arguments:
#   Warning messages to log, one or more strings
# Returns:
#   None
###########################################################################################

log_warning() {
  echo "${logname}: WARNING -" "${@}" 1>&2
}

###########################################################################################
# Git clone operation
#
# Globals:
#   force
#   logname
#   git_pat
#   git_user
#   repo_url
#   dest_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

clone_repo() {
  local git_clone_args=()
  local clone_dir
  local uri_scheme
  local uri_host
  local uri_port
  local uri_path

  if ! uri_scheme="$(/usr/local/bin/parse-uri.sh --scheme ${repo_url})"; then
    log_error "Failed to extract the scheme from ${repo_url}"
    exit 1
  fi

  if ! uri_host="$(/usr/local/bin/parse-uri.sh --host ${repo_url})"; then
    log_error "Failed to extract the host from ${repo_url}"
    exit 1
  fi

  if ! uri_port="$(/usr/local/bin/parse-uri.sh --port ${repo_url})"; then
    log_error "Failed to extract the port from ${repo_url}"
    exit 1
  fi

  if ! uri_path="$(/usr/local/bin/parse-uri.sh --path ${repo_url})"; then
    log_error "Failed to extract the path from ${repo_url}"
    exit 1
  fi

  if ! clone_dir="$(basename -s .git $(/usr/local/bin/parse-uri.sh --path ${repo_url}))"; then
    log_error "Failed to extract the clone directory from ${repo_url}"
    exit 1
  fi

  if [[ -d "${dest_dir}/${clone_dir}" && "${force}" == "on" ]]; then
    log_info "Deleting ${dest_dir}/${clone_dir}"
    if ! rm -rf "${dest_dir}/${clone_dir}"; then
      log_error "Failed to delete ${dest_dir}/${clone_dir}"
      exit 1
    fi
  elif [[ -d "${dest_dir}/${clone_dir}" ]]; then
    log_info "Cloned directory ${dest_dir}/${clone_dir} already exists, cloning" \
      "operation will be skipped."
    return 0
  fi

  if [[ ! -z "${branch}" ]]; then
    log_info "Cloning ${repo_url} to ${dest_dir} (${branch} branch)"
    git_clone_args+=("-b" "${branch}")
  else
    log_info "Cloning ${repo_url} to ${dest_dir}"
  fi

  if [[ "${single_branch}" == "on" ]]; then
    git_clone_args+=("--single-branch")
  fi

  local clone_url="${uri_scheme}://${git_user:+${git_user}${git_pat:+:${git_pat}}@}${uri_host}${uri_port:+:${uri_port}}${uri_path}"
  git_clone_args+=("${clone_url}")

  if [[ ! -n "${git_pat}" ]]; then
    log_warning "No personal access token provided, clone will fail if ${repo_url} is" \
      "not public."
  fi

  log_info "Executing git clone ${git_clone_args[@]}"

  if ! (cd "${dest_dir}" && git clone "${git_clone_args[@]}"); then
    log_error "Cloning failed, please check output"
    exit 1
  fi
}

###########################################################################################
# Change file access permissions
#
# Globals:
#   logname
#   dir_chmod_setting
#   file_chmod_setting
#   dest_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

chmod_files() {
  log_info "Recursively change directory access permissions under ${dest_dir} to" \
    "${dir_chmod_setting}"

  if ! find "${dest_dir}" -type d -print0 | xargs -0 chmod "${dir_chmod_setting}"; then
    log_error "Setting directory access permissions to ${dir_chmod_setting} failed"
    exit 1
  fi

  log_info "Recursively change file access permissions under ${dest_dir} to" \
    "${file_chmod_setting}"

  if ! find "${dest_dir}" -type f -print0 | xargs -0 chmod "${file_chmod_setting}"; then
    log_error "Setting file access permissions to ${file_chmod_setting} failed"
    exit 1
  fi
}

###########################################################################################
# Change file ownership
#
# Globals:
#   logname
#   chown_setting
#   dest_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

chown_files() {
  log_info "Recursively change ownership of ${dest_dir} to ${chown_setting}"

  if ! chown -R "${chown_setting}" "${dest_dir}"; then
    log_error "Changing ownership of ${dest_dir} to ${chown_setting} failed"
    exit 1
  fi
}

###########################################################################################
# Main script
###########################################################################################

clone_repo
chown_files
chmod_files
# ] <-- needed because of Argbash
