#!/bin/bash

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_OPTIONAL_SINGLE([env],[e],[Name of conda environment],[base])
# ARG_OPTIONAL_REPEATED([channel],[c],[Conda channel to search for packages],[])
# ARG_POSITIONAL_SINGLE([filepath],[Path to an environment.yml file],[])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Install Python modules using conda and pip at runtime\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly ai_user="${AI_USER}"
readonly ai_workdir="${AI_WORKDIR}"
readonly channel=${_arg_channel[@]}
readonly conda_dir="${CONDA_DIR}"
readonly env="${_arg_env}"
readonly filepath="${_arg_filepath}"
readonly logname="Install Python Modules"

###########################################################################################
# Read channels field
#
# Globals:
#   channel
#   filepath
# Arguments:
#   None
# Returns:
#   List of installation channels in option flag format
###########################################################################################

read_channels() {
  local env_channels="-c defaults"

  if [[ -z ${channel[@]} ]]; then
    local env_channels_list=($(yq read ${filepath} channels[*]))
    local env_channels=$(for c in ${env_channels_list[@]}; do echo "-c ${c}"; done)
  fi

  echo "${env_channels}"
}

###########################################################################################
# Install conda dependencies
#
# Globals:
#   conda_dir
#   env
#   filepath
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

install_conda_dependencies() {
  local dependencies=$(yq read ${filepath} "dependencies(.==*)")
  local channels=$(read_channels)

  if [[ ! -z ${dependencies} && ! -z ${channels} ]]; then
    echo "${logname}: installing dependencies - conda"
    echo "${logname}: channels option flags - ${channels}"
    echo "${logname}: dependencies list - ${dependencies}"

    ${conda_dir}/condabin/conda install \
      -n ${env} \
      ${channels} \
      -q \
      -y \
      ${dependencies}
  fi
}

###########################################################################################
# Install pip dependencies
#
# Globals:
#   conda_dir
#   env
#   filepath
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

install_pip_dependencies() {
  local dependencies=$(yq read ${filepath} "dependencies[*].pip[*]")

  if [[ ! -z ${dependencies} ]]; then
    echo "${logname}: installing dependencies - pip"
    echo "${logname}: dependencies list - ${dependencies}"

    ${conda_dir}/condabin/conda run -n ${env} \
      pip install --no-cache-dir ${dependencies}
  fi
}

###########################################################################################
# Clear cache and prune files
#
# Globals:
#   ai_user
#   conda_dir
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

clear_cache() {
  echo "${logname}: pruning files"

  find ${conda_dir} -follow -type f -name '*.a' -delete
  find ${conda_dir} -follow -type f -name '*.js.map' -delete
  rm -rf /home/${ai_user}/.cache/yarn

  echo "${logname}: clearing conda cache"

  ${conda_dir}/condabin/conda clean -afy
}

###########################################################################################
# Fix permissions
#
# Globals:
#   ai_user
#   ai_workdir
#   conda_dir
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

fix_permissions() {
  echo "${logname}: fixing directory permissions - ${conda_dir} ${ai_workdir} /home/${ai_user}"

  /usr/local/bin/fix-permissions.sh ${conda_dir} ${ai_workdir} /home/${ai_user}
}

###########################################################################################
# Main script
###########################################################################################

install_conda_dependencies
install_pip_dependencies
clean_cache
fix_permissions
# ] <-- needed because of Argbash
