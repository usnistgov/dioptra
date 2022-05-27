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
# ARG_OPTIONAL_SINGLE([conda-env],[],[Conda environment],[dioptra])
# ARG_OPTIONAL_SINGLE([output],[o],[Path to save exported environment.yml file (ignored unless paired with --export-conda-env)],[])
# ARG_OPTIONAL_SINGLE([results-ttl],[],[Job results will be kept for this number of seconds],[500])
# ARG_OPTIONAL_SINGLE([rq-worker-module],[],[Python module used to start the RQ Worker],[dioptra.rq.cli.rq])
# ARG_OPTIONAL_BOOLEAN([export-conda-env],[],[Freeze and export the container's conda environment (--output must be set)])
# ARG_LEFTOVERS([Queues to watch])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Dioptra Worker Entry Point\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly conda_dir="${CONDA_DIR}"
readonly conda_env="${_arg_conda_env}"
readonly dioptra_workdir="${DIOPTRA_WORKDIR}"
readonly export_conda_env="${_arg_export_conda_env}"
readonly job_queues="${_arg_leftovers[*]}"
readonly logname="Container Entry Point"
readonly rq_worker_module="${_arg_rq_worker_module}"
readonly rq_redis_uri="${RQ_REDIS_URI-}"
readonly rq_results_ttl="${_arg_results_ttl}"

###########################################################################################
# Secure the container at runtime
#
# Globals:
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

secure_container() {
  if [[ -f /usr/local/bin/secure-container.sh ]]; then
    /usr/local/bin/secure-container.sh
  else
    echo "${logname}: ERROR - /usr/local/bin/secure-container.sh script missing" 1>&2
    exit 1
  fi
}

###########################################################################################
# Freeze and export the worker's conda virtual environment
#
# Globals:
#   conda_env
#   logname
#   _arg_output
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

export_conda_environment() {
  if [[ ! -f /usr/local/bin/conda-env.sh ]]; then
    echo "${logname}: ERROR - /usr/local/bin/conda-env.sh script missing" 1>&2
    exit 1
  fi

  if ! /usr/local/bin/conda-env.sh --env ${conda_env} --output ${_arg_output} --freeze; then
    exit 1
  fi
}

###########################################################################################
# Start Redis Queue Worker
#
# Globals:
#   conda_dir
#   conda_env
#   dioptra_workdir
#   job_queues
#   logname
#   rq_redis_uri
#   rq_results_ttl
#   rq_worker_module
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_rq() {
  echo "${logname}: starting rq worker"
  echo "${logname}: rq worker --url ${rq_redis_uri} --results-ttl ${rq_results_ttl} \
  ${job_queues}"

  bash -c "\
  source ${conda_dir}/etc/profile.d/conda.sh &&\
  conda activate ${conda_env} &&\
  cd ${dioptra_workdir} &&\
  python -m ${rq_worker_module} worker\
  --url ${rq_redis_uri}\
  --results-ttl ${rq_results_ttl}\
  ${job_queues}"
}

###########################################################################################
# The top-level function in the script
#
# Globals:
#   export_conda_env
#   logname
#   _arg_output
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

main() {
  case "${export_conda_env}" in
    on)
      export_conda_environment
      ;;
    off)
      secure_container
      start_rq
      ;;
    *)
      echo "${logname}: ERROR - Unexcepted value of export_conda_env"
        "'${export_conda_env}'." 1>&2
      exit 1
      ;;
  esac
}

###########################################################################################
# Main script
###########################################################################################

main
# ] <-- needed because of Argbash
