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
SCRIPT_DIRPATH="$(realpath ${0%%/*})"
LOGNAME="Docker Image Build"

CREATED_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
REVISION="$(git log -1 --pretty=%H)"
REPO_URL="https://github.com/usnistgov/dioptra"
DOCS_URL="https://pages.nist.gov/dioptra"
IMAGE_AUTHORS="NCCoE Artificial Intelligence Team <dioptra@nist.gov>, James Glasbrenner <jglasbrenner@mitre.org>, Harold Booth <harold.booth@nist.gov>, Keith Manville <kmanville@mitre.org>, Julian Sexton <jtsexton@mitre.org>, Michael Andy Chisholm, Henry Choy <hchoy@mitre.org>, Andrew Hand <ahand@mitre.org>, Bronwyn Hodges <bhodges@mitre.org>, Paul Scemama, Dmitry Cousin <dmitry.cousin@nist.gov>, Eric Trapnell <eric.trapnell@nist.gov>, Mark Trapnell <mark.trapnell@nist.gov>, Howard Huang <hhuang@mitre.org>, Paul Rowe <prowe@mitre.org>, Alexander Byrne <alexanderbyrne@mitre.org>, Luke Barner, Cory Miniter"
IMAGE_VENDOR="National Institute of Standards and Technology"
IMAGE_LICENSE="NIST-PD OR CC-BY-4.0"

DEFAULT_ARG_BUILD_CONTEXT="."
DEFAULT_ARG_CONTAINERS_FOLDER="docker"
DEFAULT_ARG_DOCKERFILE_SUFFIX="restapi"
DEFAULT_ARG_IMAGE_PREFIX="dioptra"
DEFAULT_ARG_IMAGE_TAG="dev"
DEFAULT_ARG_BUILD_TARGET="final"
DEFAULT_ARG_TARGETARCH="amd64"
DEFAULT_ARG_NO_CACHE="off"

_arg_build_context="${DEFAULT_ARG_BUILD_CONTEXT}"
_arg_containers_folder="${DEFAULT_ARG_CONTAINERS_FOLDER}"
_arg_dockerfile_suffix="${DEFAULT_ARG_DOCKERFILE_SUFFIX}"
_arg_image_prefix="${DEFAULT_ARG_IMAGE_PREFIX}"
_arg_image_tag="${DEFAULT_ARG_IMAGE_TAG}"
_arg_build_target="${DEFAULT_ARG_BUILD_TARGET}"
_arg_targetarch="${DEFAULT_ARG_TARGETARCH}"
_arg_no_cache="${DEFAULT_ARG_NO_CACHE}"

###########################################################################################
# Print the script help message
#
# Globals:
#   DEFAULT_ARG_BUILD_CONTEXT
#   DEFAULT_ARG_CONTAINERS_FOLDER
#   DEFAULT_ARG_DOCKERFILE_SUFFIX
#   DEFAULT_ARG_IMAGE_PREFIX
#   DEFAULT_ARG_IMAGE_TAG
#   DEFAULT_ARG_BUILD_TARGET
#   DEFAULT_ARG_TARGETARCH
# Arguments:
#   Error messages to log, a string
# Returns:
#   None
###########################################################################################

print_help() {
  cat <<-HELPMESSAGE
		Build a Dockerfile image.

		Usage: build-container.sh [--build_context <arg>] [--containers-folder <arg>]
		                          [--dockerfile-suffix [mlflow-tracking|nginx|pytorch-cpu
		                                                |pytorch-gpu|restapi|tensorflow2-cpu
		                                                |tensorflow2-gpu]]
		                          [--image-tag <arg>] [--build-target <arg>]
		                          [--image-prefix <arg>] [--targetarch [amd64|arm64]]
		                          [--no-cache] [-h|--help]
		        --build_context: Path to the build context
		                         (default: '${DEFAULT_ARG_BUILD_CONTEXT}')
		        --containers-folder: Path to the folder containing the Dockerfiles
		                             (default: '${DEFAULT_ARG_CONTAINERS_FOLDER}')
		        --dockerfile-suffix: Suffix of the Dockerfile to build, must be one of
		                                'mlflow-tracking', 'nginx', 'pytorch-cpu',
		                                'pytorch-gpu', 'restapi', 'tensorflow2-cpu', or
		                                'tensorflow2-gpu'
		                                (default: '${DEFAULT_ARG_DOCKERFILE_SUFFIX}')
		        --image-tag: Tag to give to built image (default: '${DEFAULT_ARG_IMAGE_TAG}')
		        --build-target: Target in multi-stage build (default: '${DEFAULT_ARG_BUILD_TARGET}')
		        --image-prefix: Image name prefix (default: '${DEFAULT_ARG_IMAGE_PREFIX}')
		        --targetarch: Target architecture of build (default: '${DEFAULT_ARG_TARGETARCH}')
		        --no-cache: Do not use cache when building the image
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
# Validate the value passed to the --targetarch argument
#
# Globals:
#   None
# Arguments:
#   The target architecture
# Returns:
#   None
###########################################################################################

validate_targetarch() {
  local targetarch="${1}"

  case "${targetarch}" in
    amd64 | arm64)
      return 0
      ;;
    *)
      log_error "Unrecognized value ${targetarch} for --targetarch, must be one of" \
        "['amd64', 'arm64'], exiting..."
      exit 1
      ;;
  esac
}

###########################################################################################
# Validate the value passed to the --dockerfile-suffix argument
#
# Globals:
#   None
# Arguments:
#   The dockerfile suffix
# Returns:
#   None
###########################################################################################

validate_dockerfile_suffix() {
  local dockerfile_suffix="${1}"

  case "${dockerfile_suffix}" in
    mlflow-tracking | nginx | pytorch-cpu | pytorch-gpu | restapi | tensorflow2-cpu | tensorflow2-gpu)
      return 0
      ;;
    *)
      log_error "Unrecognized value ${dockerfile_suffix} for --dockerfile-suffix, " \
        "must be one of ['mlflow-tracking', 'nginx', pytorch-cpu', 'pytorch-gpu', " \
        "'restapi', 'tensorflow2-cpu', 'tensorflow2-gpu'], " \
        "exiting..."
      exit 1
      ;;
  esac
}

###########################################################################################
# Validate Dockerfile exists
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_dockerfile_exists() {
  local dockerfile="${_arg_containers_folder}/Dockerfile.${_arg_dockerfile_suffix}"

  if [[ ! -f "${dockerfile}" ]]; then
    log_error "Dockerfile ${dockerfile} not found, exiting..."
    exit 1
  fi
}

###########################################################################################
# Wrapper for invoking docker
#
# Globals:
#   None
# Arguments:
#   Positional arguments, one or more strings
# Returns:
#   None
###########################################################################################

docker_cmd() {
  if ! docker "${@}"; then
    log_error "Encountered an error when executing docker, exiting..."
    exit 1
  fi
}

###########################################################################################
# Parse the script arguments
#
# Globals:
#   _arg_build_context
#   _arg_containers_folder
#   _arg_dockerfile_suffix
#   _arg_image_prefix
#   _arg_image_tag
#   _arg_build_target
#   _arg_targetarch
#   _arg_no_cache
# Arguments:
#   Script arguments, an array
# Returns:
#   None
###########################################################################################

parse_args() {
  while (("${#}" > 0)); do
    case "${1}" in
      -h | --help)
        print_help
        exit 0
        ;;
      --build-context)
        _arg_build_context="${2}"
        shift 2
        ;;
      --containers-folder)
        _arg_containers_folder="${2}"
        shift 2
        ;;
      --dockerfile-suffix)
        validate_dockerfile_suffix "${2}"
        _arg_dockerfile_suffix="${2}"
        shift 2
        ;;
      --image-prefix)
        _arg_image_prefix="${2}"
        shift 2
        ;;
      --image-tag)
        _arg_image_tag="${2}"
        shift 2
        ;;
      --build-target)
        _arg_build_target="${2}"
        shift 2
        ;;
      --targetarch)
        validate_targetarch "${2}"
        _arg_targetarch="${2}"
        shift 2
        ;;
      --no-cache)
        _arg_no_cache="on"
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
# Build the Dockerfile image
#
# Globals:
#   CREATED_DATE
#   DOCS_URL
#   IMAGE_AUTHORS
#   IMAGE_VENDOR
#   REPO_URL
#   _arg_build_context
#   _arg_build_target
#   _arg_dockerfile_suffix
#   _arg_containers_folder
#   _arg_image_prefix
#   _arg_image_tag
#   _arg_no_cache
#   _arg_targetarch
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

docker_build() {
  local dockerfile="${_arg_containers_folder}/Dockerfile.${_arg_dockerfile_suffix}"
  local image_tag="${_arg_image_prefix}/${_arg_dockerfile_suffix}:${_arg_image_tag}"
  local args=(
    "--tag"
    "${image_tag}"
    "-f"
    "${dockerfile}"
    "--target"
    "${_arg_build_target}"
    "--platform"
    "linux/${_arg_targetarch}"
    "--label"
    "org.opencontainers.image.title=${_arg_dockerfile_suffix}"
    "--label"
    "org.opencontainers.image.description=Provides the ${_arg_dockerfile_suffix} service."
    "--label"
    "org.opencontainers.image.authors=${IMAGE_AUTHORS}"
    "--label"
    "org.opencontainers.image.vendor=${IMAGE_VENDOR}"
    "--label"
    "org.opencontainers.image.url=${REPO_URL}"
    "--label"
    "org.opencontainers.image.source=${REPO_URL}"
    "--label"
    "org.opencontainers.image.documentation=${DOCS_URL}"
    "--label"
    "org.opencontainers.image.version=${_arg_image_tag}"
    "--label"
    "org.opencontainers.image.created=${CREATED_DATE}"
    "--label"
    "org.opencontainers.image.revision=${REVISION}"
    "--label"
    "org.opencontainers.image.licenses=${IMAGE_LICENSE}"
  )

  if [[ "${_arg_no_cache}" == "on" ]]; then
    args+=("--no-cache")
  fi

  args+=("${_arg_build_context}")

  log_info "Building ${dockerfile}"

  if ! docker_cmd build "${args[@]}"; then
    log_error "Encountered an error when building the Dockerfile ${dockerfile}," \
      "exiting..."
    exit 1
  fi
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
  validate_dockerfile_exists
  docker_build
}

###########################################################################################
# Main script
###########################################################################################

main "${@}"
