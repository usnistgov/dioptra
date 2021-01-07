#!/bin/bash

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_OPTIONAL_SINGLE([data-dir],[],[Data directory relative to current directory],[data])
# ARG_OPTIONAL_SINGLE([image],[],[GPU-enabled docker image to use for running a job],[securing-ai/tensorflow2-gpu-py37:0.0.0-1])
# ARG_OPTIONAL_SINGLE([gpu-devices],[],[Specify the exact GPU devices to use, overrides num-gpus],[])
# ARG_OPTIONAL_SINGLE([gpu-num],[],[Set the GPU devices to use],[1])
# ARG_OPTIONAL_SINGLE([mlflow-uri],[],[MLFlow Tracking URI],[http://mlflow-tracking-username:5000])
# ARG_OPTIONAL_SINGLE([name],[],[Experiment name],[mnist])
# ARG_OPTIONAL_SINGLE([network],[],[Docker network to attach to],[tensorflow-mnist-classifier_username])
# ARG_OPTIONAL_SINGLE([s3-uri],[],[S3 endpoint URI],[http://minio-username:9000])
# ARG_OPTIONAL_SINGLE([s3-user],[],[Username for S3 storage],[minio])
# ARG_OPTIONAL_SINGLE([s3-pass],[],[Password for S3 storage],[minio123])
# ARG_LEFTOVERS([Entry point keyword arguments (optional)])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Run a MLFlow job using a GPU-enabled container.\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly data_dir="$(pwd)/${_arg_data_dir}"
readonly docker_image="${_arg_image}"
readonly entry_point_kwargs="${_arg_leftovers[*]}"
readonly gpu_devices="${_arg_gpu_devices}"
readonly gpu_num="${_arg_gpu_num}"
readonly mlflow_uri="${_arg_mlflow_uri}"
readonly experiment_name="${_arg_name}"
readonly network="${_arg_network}"
readonly s3_uri="${_arg_s3_uri}"
readonly s3_user="${_arg_s3_user}"
readonly s3_pass="${_arg_s3_pass}"
readonly logname="docker-gpu run"

###########################################################################################
# Get the --gpus option for docker run
#
# Globals:
#   gpu_devices
#   gpu_num
# Arguments:
#   None
# Returns:
#   String to be passed to the docker run --gpus option
###########################################################################################

gpus_option_value() {
  local gpus="${gpu_num}"

  if [[ ! -z ${gpu_devices} ]]; then
    gpus=\"device=${gpu_devices}\"
  fi

  echo "${gpus}"
}

###########################################################################################
# Create bucket on S3 storage
#
# Globals:
#   data_dir
#   docker_image
#   entry_point_kwargs
#   experiment_name
#   mlflow_uri
#   network
#   s3_uri
#   s3_user
#   s3_pass
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

docker_gpu_run() {
  local gpus=$(gpus_option_value)

  echo "${logname}: Starting GPU-enabled container using ${docker_image}"

  docker run --rm -it --gpus ${gpus} \
    --volume "${data_dir}:/nfs/data" \
    -e "AWS_ACCESS_KEY_ID=${s3_user}" \
    -e "AWS_SECRET_ACCESS_KEY=${s3_pass}" \
    -e "MLFLOW_EXPERIMENT_NAME=${experiment_name}" \
    -e "MLFLOW_TRACKING_URI=${mlflow_uri}" \
    -e "MLFLOW_S3_ENDPOINT_URL=${s3_uri}" \
    --network=${network} \
    ${docker_image} \
    ${entry_point_kwargs}
}

###########################################################################################
# Main script
###########################################################################################

docker_gpu_run
# ] <-- needed because of Argbash
