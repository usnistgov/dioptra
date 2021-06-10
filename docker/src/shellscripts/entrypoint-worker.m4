#!/bin/bash
# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_OPTIONAL_SINGLE([conda-env],[],[Conda environment],[mitre-securing-ai])
# ARG_OPTIONAL_SINGLE([results-ttl],[],[Job results will be kept for this number of seconds],[500])
# ARG_OPTIONAL_SINGLE([rq-worker-module],[],[Python module used to start the RQ Worker],[mitre.securingai.rq.cli.rq])
# ARG_LEFTOVERS([Queues to watch])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Securing AI Worker Entry Point\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly ai_workdir="${AI_WORKDIR}"
readonly conda_dir="${CONDA_DIR}"
readonly conda_env="${_arg_conda_env}"
readonly job_queues="${_arg_leftovers[*]}"
readonly logname="Container Entry Point"
readonly rq_worker_module="${_arg_rq_worker_module}"
readonly rq_redis_uri="${RQ_REDIS_URI-}"
readonly rq_results_ttl="${_arg_results_ttl}"

###########################################################################################
# Secure the container at runtime
#
# Globals:
#   None
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
# Start Redis Queue Worker
#
# Globals:
#   ai_workdir
#   conda_dir
#   conda_env
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
  cd ${ai_workdir} &&\
  python -m ${rq_worker_module} worker\
  --url ${rq_redis_uri}\
  --results-ttl ${rq_results_ttl}\
  ${job_queues}"
}

###########################################################################################
# Main script
###########################################################################################

secure_container
start_rq
# ] <-- needed because of Argbash
