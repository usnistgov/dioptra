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
# ARG_OPTIONAL_SINGLE([file],[f],[Path to environment.yml template],[])
# ARG_OPTIONAL_SINGLE([output],[o],[Path to save rendered environment.yml file],[])
# ARG_OPTIONAL_SINGLE([ibm-art-version],[],[Pin version of IBM Adversarial Robustness Toolbox library],[])
# ARG_OPTIONAL_SINGLE([mlflow-version],[],[Pin version of MLflow library],[])
# ARG_OPTIONAL_SINGLE([prefect-version],[],[Pin version of Prefect library],[])
# ARG_OPTIONAL_SINGLE([python-version],[],[Pin version of Python interpreter],[])
# ARG_OPTIONAL_SINGLE([pytorch-cuda-version],[],[Pin version of CUDA used with PyTorch library],[])
# ARG_OPTIONAL_SINGLE([pytorch-major-minor-version],[],[Pin major/minor version of PyTorch library],[])
# ARG_OPTIONAL_SINGLE([pytorch-torchaudio-version],[],[Pin version of Torchaudio library],[])
# ARG_OPTIONAL_SINGLE([pytorch-torchvision-version],[],[Pin version of Torchvision library],[])
# ARG_OPTIONAL_SINGLE([pytorch-version],[],[Pin version of PyTorch library],[])
# ARG_OPTIONAL_SINGLE([sklearn-version],[],[Pin version of scikit-learn library],[])
# ARG_OPTIONAL_SINGLE([tensorflow-version],[],[Pin version of Tensorflow library],[])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Conda environment template rendering tool\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly ibm_art_version="${_arg_ibm_art_version}"
readonly mlflow_version="${_arg_mlflow_version}"
readonly prefect_version="${_arg_prefect_version}"
readonly python_version="${_arg_python_version}"
readonly pytorch_cuda_version="${_arg_pytorch_cuda_version}"
readonly pytorch_major_minor_version="${_arg_pytorch_major_minor_version}"
readonly pytorch_torchaudio_version="${_arg_pytorch_torchaudio_version}"
readonly pytorch_torchvision_version="${_arg_pytorch_torchvision_version}"
readonly pytorch_version="${_arg_pytorch_version}"
readonly sklearn_version="${_arg_sklearn_version}"
readonly tensorflow_version="${_arg_tensorflow_version}"
readonly logname="Render conda environment template"

###########################################################################################
# Use yq tool to render a Dioptra environment.yml template
#
# Globals:
#   ibm_art_version
#   mlflow_version
#   prefect_version
#   python_version
#   pytorch_major_minor_version
#   pytorch_version
#   pytorch_cuda_version
#   pytorch_torchaudio_version
#   pytorch_torchvision_version
#   sklearn_version
#   tensorflow_version
#   _arg_file
#   _arg_output
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

yq_render_environment_yml_template() {
  /usr/local/bin/yq --no-colors --prettyPrint eval \
    "(.dependencies[] | select(. == \"python\")) = \"python=${python_version}\" | \
      (.dependencies[] | select(. == \"scikit-learn\")) = \"scikit-learn=${sklearn_version}\" | \
      (.dependencies[].pip[] | select(. == \"adversarial-robustness-toolbox\")) = \"adversarial-robustness-toolbox==${ibm_art_version}\" | \
      (.dependencies[].pip[] | select(. == \"mlflow\")) = \"mlflow==${mlflow_version}\" | \
      (.dependencies[].pip[] | select(. == \"prefect\")) = \"prefect==${prefect_version}\" | \
      (.dependencies[].pip[] | select(. == \"tensorflow\")) = \"tensorflow==${tensorflow_version}\" | \
      (.dependencies[].pip[] | select(. == \"tensorflow-cpu\")) = \"tensorflow-cpu==${tensorflow_version}\" | \
      (.dependencies[].pip[] | select(test(\"--find-links.*$\"))) |= sub(\"{{PYTORCH_MAJOR_MINOR_VERSION}}\", \"${pytorch_major_minor_version}\") | \
      (.dependencies[].pip[] | select(test(\"--find-links.*$\"))) |= sub(\"{{PYTORCH_CUDA_VERSION}}\", \"${pytorch_cuda_version}\") | \
      (.dependencies[].pip[] | select(. == \"torch\" and line_comment == \"cpu\")) = \"torch==${pytorch_version}+cpu\" | \
      (.dependencies[].pip[] | select(. == \"torchvision\" and line_comment == \"cpu\")) = \"torchvision==${pytorch_torchvision_version}+cpu\" | \
      (.dependencies[].pip[] | select(. == \"torchaudio\" and line_comment == \"cpu\")) = \"torchaudio==${pytorch_torchaudio_version}+cpu\" | \
      (.dependencies[].pip[] | select(. == \"torch\" and line_comment == \"gpu\")) = \"torch==${pytorch_version}+${pytorch_cuda_version}\" | \
      (.dependencies[].pip[] | select(. == \"torchvision\" and line_comment == \"gpu\")) = \"torchvision==${pytorch_torchvision_version}+${pytorch_cuda_version}\" | \
      (.dependencies[].pip[] | select(. == \"torchaudio\" and line_comment == \"gpu\")) = \"torchaudio==${pytorch_torchaudio_version}+${pytorch_cuda_version}\" | \
      (.dependencies[].pip[] | select(line_comment == \"cpu\" or line_comment == \"gpu\")) |= . line_comment=\"\"" \
    ${_arg_file} > ${_arg_output}
}

###########################################################################################
# The top-level function in the script
#
# Globals:
#   logname
#   _arg_file
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

main() {
  if [[ ! $(command -v /usr/local/bin/yq) ]]; then
    echo "${logname}: ERROR - Cannot find yq binary" 1>&2
    exit 1
  fi

  if ! yq_render_environment_yml_template; then
    echo "${logname}: ERROR - Failed to render ${_arg_file}" 1>&2
  fi
}

###########################################################################################
# Main script
###########################################################################################

main
# ] <-- needed because of Argbash
