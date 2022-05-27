#!/bin/bash

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_OPTIONAL_SINGLE([env],[e],[Name of the conda environment to export (--freeze only)],[])
# ARG_OPTIONAL_SINGLE([file],[f],[Path to existing environment.yml file],[])
# ARG_OPTIONAL_SINGLE([output],[o],[Path to save exported environment.yml file],[])
# ARG_OPTIONAL_BOOLEAN([strict],[],[Force non-zero exit for warnings])
# ARG_OPTIONAL_ACTION([create],[],[Create a new conda environment (--file must be set)],[create_conda_environment])
# ARG_OPTIONAL_ACTION([update],[],[Update an existing conda environment (--file must be set)],[update_conda_environment])
# ARG_OPTIONAL_ACTION([freeze],[],[Export the current conda environment (--env and --output must be set)],[freeze_conda_environment])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Manage the conda virtual environment\n])"
# ARGBASH_PREPARE

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

readonly conda_dir="${CONDA_DIR}"
readonly logname="Conda Environment"

###########################################################################################
# Count the number of times a name has an exact match in `conda env list`
#
# Globals:
#   logname
#   conda_dir
# Arguments:
#   Environment name to count, a string
# Outputs:
#   Writes the number of times the environment name was found to stdout
# Returns:
#   0 if num_name_matches is zero or one, 1 if it is greater than one
###########################################################################################

count_conda_environment_name_matches() {
  local env_name="${1}"
  local name_matches=()
  local num_name_matches

  while IFS= read -r line; do
    [[ $line =~ ^\#.* ]] && continue
    [[ "${line}" =~ ^"${env_name}"[[:space:]]+ ]] && name_matches+=(${env_name})
  done < <(${conda_dir}/condabin/conda env list)

  num_name_matches="${#name_matches[@]}"

  if ((${num_name_matches} > 1)); then
    echo "${logname}: WARNING - More than one instance of the environment name" \
      "${env_name} was found in the output of 'conda env list'. Number found =" \
      "${num_name_matches}" 1>&2
    echo "${num_name_matches}"
    return 1
  fi

  echo "${num_name_matches}"
  return 0
}

###########################################################################################
# Validate --file parameter
#
# Globals:
#   logname
#   _arg_file
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_file_parameter() {
  if [[ ! -n ${_arg_file} ]]; then
    echo "${logname}: ERROR - No environment.yml file provided. Please specify the" \
      "environment file using --file and try again." 1>&2
    exit 1
  fi

  if [[ ! -f ${_arg_file} ]]; then
    echo "${logname}: ERROR - Unable to read the file ${_arg_file}." 1>&2
    exit 1
  fi
}

###########################################################################################
# Validate --output parameter
#
# Globals:
#   logname
#   _arg_output
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_output_parameter() {
  if [[ -f ${_arg_output} ]]; then
    echo "${logname}: ERROR - A file already exists at ${_arg_output}. Please choose a" \
      "different output file using --output and try again." 1>&2
    exit 1
  fi
}

###########################################################################################
# Validate that the environment passed to --env exists
#
# Globals:
#   logname
#   _arg_env
#   conda_dir
# Arguments:
#   None
# Returns:
#   0 if num_name_matches is zero or one, 1 if it is greater than one
###########################################################################################

validate_env_exists() {
  local num_name_matches

  num_name_matches="$(count_conda_environment_name_matches ${_arg_env})"
  return_code="$?"

  if [[ ${num_name_matches} == 0 ]]; then
    echo "${logname}: ERROR - The environment ${_arg_env} does not exist." 1>&2
    exit 1
  fi

  return ${return_code}
}

###########################################################################################
# Validate that the environment in environment.yml does not exist
#
# Globals:
#   logname
#   _arg_file
#   conda_dir
# Arguments:
#   None
# Returns:
#   0 if num_name_matches is zero or one, 1 if it is greater than one
###########################################################################################

validate_env_in_environment_yml_does_not_exist() {
  local env_name
  local num_name_matches
  local return_code

  if ! env_name="$(cat ${_arg_file} | grep --color=never -oP "name:\s+\K\w+$")"; then
    echo "${logname}: ERROR - Failed to grep the environment name from" \
      "${_arg_file}." 1>&2
    exit 1
  fi

  num_name_matches="$(count_conda_environment_name_matches ${env_name})"
  return_code="$?"

  if [[ ${num_name_matches} == 1 ]]; then
    echo "${logname}: ERROR - The environment ${env_name} already exists. Please use" \
      "--update instead of --create and try again." 1>&2
    exit 1
  fi

  return ${return_code}
}

###########################################################################################
# Validate that the environment in environment.yml exists
#
# Globals:
#   logname
#   _arg_file
#   conda_dir
# Arguments:
#   None
# Returns:
#   0 if num_name_matches is zero or one, 1 if it is greater than one
###########################################################################################

validate_env_in_environment_yml_exists() {
  local env_name
  local num_name_matches

  if ! env_name="$(cat ${_arg_file} | grep --color=never -oP "name:\s+\K\w+$")"; then
    echo "${logname}: ERROR - Failed to grep the environment name from" \
      "${_arg_file}." 1>&2
    exit 1
  fi

  num_name_matches="$(count_conda_environment_name_matches ${env_name})"
  return_code="$?"

  if [[ ${num_name_matches} == 0 ]]; then
    echo "${logname}: ERROR - The environment ${env_name} does not exist. Please use" \
      "--create instead of --update and try again." 1>&2
    exit 1
  fi

  return ${return_code}
}

###########################################################################################
# Fix directory permissions
#
# Globals:
#   logname
#   conda_dir
#   virtualenvs_dir
# Arguments:
#   None
# Returns:
#   0 if fix-permissions.sh succeeds, 1 if it fails
###########################################################################################

fix_permissions() {
  if [[ ! -f /usr/local/bin/fix-permissions.sh ]]; then
    echo "${logname}: ERROR - /usr/local/bin/fix-permissions.sh script missing" 1>&2
    exit 1
  fi

  if ! /usr/local/bin/fix-permissions.sh ${HOME} ${conda_dir} ${virtualenvs_dir}; then
    echo "${logname}: WARNING - The fix permissions script encountered an error, please" \
      "check output." 1>&2
    return 1
  fi

  return 0
}

###########################################################################################
# Clean the conda environment
#
# Globals:
#   logname
#   conda_dir
#   virtualenvs_dir
# Arguments:
#   None
# Returns:
#   A count of the number of warnings encountered, 0 if there were no warnings
###########################################################################################

clean_conda() {
  local error_count=0

  for dirname in ${conda_dir} ${virtualenvs_dir}; do
    if ! find ${dirname} -follow -type f -name '*.a' -delete; then
      echo "${logname}: WARNING - Failed to find and remove '*.a' files in ${dirname}" 1>&2
      ((error_count += 1))
    fi

    if ! find ${dirname} -follow -type f -name '*.js.map' -delete; then
      echo "${logname}: WARNING - Failed to find and remove '*.js.map' files in" \
        "${dirname}" 1>&2
      ((error_count += 1))
    fi
  done

  if ! ${conda_dir}/condabin/conda clean -afy; then
    echo "${logname}: WARNING - Failed while running 'conda clean -afy'" 1>&2
    ((error_count += 1))
  fi

  for dirname in "${HOME}/.cache/pip" "${HOME}/.cache/yarn"; do
    if ! $(rm -r ${dirname} 2>/dev/null); then
      echo "${logname}: INFO - ${dirname} does not exist, skipping removal"
    fi
  done

  fix_permissions
  ((error_count += $?))

  return ${error_count}
}

###########################################################################################
# Create conda environment from environment.yml file
#
# Globals:
#   logname
#   _arg_file
#   _arg_strict
#   conda_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

create_conda_environment() {
  validate_file_parameter
  if (($? != 0)); then
    [[ "${_arg_strict}" == "on" ]] && exit 1
  fi

  validate_env_in_environment_yml_does_not_exist
  if (($? != 0)); then
    [[ "${_arg_strict}" == "on" ]] && exit 1
  fi

  echo "${logname}: INFO - Creating conda environment using the file ${_arg_file}."
  if ! (
    ln -s ${_arg_file} /tmp/environment.yml &&
      ${conda_dir}/condabin/conda env create --file /tmp/environment.yml &&
      rm /tmp/environment.yml
  ); then
    echo "${logname}: ERROR - Encountered an error while trying to create new virtual" \
      "environment" 1>&2
    exit 1
  fi

  echo "${logname}: INFO - Post-create conda clean-up."
  clean_conda
  if (($? != 0)); then
    [[ "${_arg_strict}" == "on" ]] && exit 1
  fi
}

###########################################################################################
# Update conda environment using environment.yml file
#
# Globals:
#   logname
#   _arg_file
#   conda_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

update_conda_environment() {
  validate_file_parameter
  if (($? != 0)); then
    [[ "${_arg_strict}" == "on" ]] && exit 1
  fi

  validate_env_in_environment_yml_exists
  if (($? != 0)); then
    [[ "${_arg_strict}" == "on" ]] && exit 1
  fi

  echo "${logname}: INFO - Updating conda environment using the file ${_arg_file}."
  if ! (
    ln -s ${_arg_file} /tmp/environment.yml &&
      ${conda_dir}/condabin/conda env update --file /tmp/environment.yml --prune &&
      rm /tmp/environment.yml
  ); then
    echo "${logname}: ERROR - Encountered an error while trying to update an existing" \
      "virtual environment" 1>&2
    exit 1
  fi

  echo "${logname}: INFO - Post-update conda clean-up."
  clean_conda
  if (($? != 0)); then
    [[ "${_arg_strict}" == "on" ]] && exit 1
  fi
}

###########################################################################################
# Export the current conda environment
#
# Globals:
#   logname
#   _arg_env
#   _arg_output
#   conda_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

freeze_conda_environment() {
  local environment_yml

  validate_output_parameter
  if (($? != 0)); then
    [[ "${_arg_strict}" == "on" ]] && exit 1
  fi

  validate_env_exists
  if (($? != 0)); then
    [[ "${_arg_strict}" == "on" ]] && exit 1
  fi

  echo "${logname}: INFO - Freeze conda environment ${_arg_env} and export to" \
    "${_arg_output}."

  if ! (
    ${conda_dir}/condabin/conda env export --name ${_arg_env} |
      sed "/^prefix:\|^[[:blank:]]*-[[:blank:]]*dioptra/d" >${_arg_output}
  ); then
    echo "${logname}: ERROR - Encountered an error while trying to freeze the" \
      "${_arg_env} virtual environment and export it to ${_arg_output}" 1>&2
    exit 1
  fi
}

###########################################################################################
# Main script
###########################################################################################

parse_commandline "$@"
print_help

# ] <-- needed because of Argbash
