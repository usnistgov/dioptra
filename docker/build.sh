#!/bin/bash

echo ""
echo "------------- ENV variables --------------------"
echo "CORES=${CORES}"
echo "DOCKER_NO_CACHE=${DOCKER_NO_CACHE}"
echo "DOCKER_BUILD_TARGET=${DOCKER_BUILD_TARGET}"
echo "DOCKER_BUILDKIT_VALUE=${DOCKER_BUILDKIT_VALUE}"
echo "DOCKER_BUILDKIT_INLINE_CACHE_VALUE=${DOCKER_BUILDKIT_INLINE_CACHE_VALUE}"
echo "IMAGE_TAG=${IMAGE_TAG}"
echo "CODE_PKG_VERSION=${CODE_PKG_VERSION}"
echo "MINICONDA3_PREFIX=${MINICONDA3_PREFIX}"
echo "MINICONDA_VERSION=${MINICONDA_VERSION}"
echo "IBM_ART_VERSION=${IBM_ART_VERSION}"
echo "MLFLOW_VERSION=${MLFLOW_VERSION}"
echo "PREFECT_VERSION=${PREFECT_VERSION}"
echo "PYTHON_VERSION=${PYTHON_VERSION}"
echo "PYTORCH_CUDA_VERSION=${PYTORCH_CUDA_VERSION}"
echo "PYTORCH_MAJOR_MINOR_VERSION=${PYTORCH_MAJOR_MINOR_VERSION}"
echo "PYTORCH_TORCHAUDIO_VERSION=${PYTORCH_TORCHAUDIO_VERSION}"
echo "PYTORCH_TORCHVISION_VERSION=${PYTORCH_TORCHVISION_VERSION}"
echo "PYTORCH_VERSION=${PYTORCH_VERSION}"
echo "SKLEARN_VERSION=${SKLEARN_VERSION}"
echo "TENSORFLOW_VERSION=${TENSORFLOW_VERSION}"
echo "PYTORCH_NVIDIA_CUDA_VERSION=${PYTORCH_NVIDIA_CUDA_VERSION}"
echo "TENSORFLOW_NVIDIA_CUDA_VERSION=${TENSORFLOW_NVIDIA_CUDA_VERSION}"
echo ""

prefix=${PROJECT_PREFIX}

echo ""
echo "Building ${prefix}/${PROJECT_COMPONENT}"
echo "=========================================="
echo ""

DOCKERFILE="docker/Dockerfile.${PROJECT_COMPONENT}"
BUILD_CONTEXT="."
BUILD_ARGS=""
IMAGE_NAME="${prefix}/${PROJECT_COMPONENT}"
CREATED_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
REVISION="$(git log -1 --pretty=%H)"

if [[ ${DOCKER_BUILDKIT_INLINE_CACHE_VALUE} == 1 ]]; then
  BUILD_ARG_BUILDKIT_INLINE_CACHE="--build-arg BUILDKIT_INLINE_CACHE=1"
else
  BUILD_ARG_BUILDKIT_INLINE_CACHE=""
fi

if [[ -e ${DOCKERFILE} ]]; then
  DOCKER_BUILDKIT=${DOCKER_BUILDKIT_VALUE} \
    docker build ${DOCKER_NO_CACHE} \
    --tag ${IMAGE_NAME}:${IMAGE_TAG} \
    -f ${DOCKERFILE} \
    --target ${DOCKER_BUILD_TARGET} ${BUILD_ARG_BUILDKIT_INLINE_CACHE} \
    --build-arg CORES=${CORES} \
    --build-arg CODE_PKG_VERSION=${CODE_PKG_VERSION} \
    --build-arg MINICONDA3_PREFIX=${MINICONDA3_PREFIX} \
    --build-arg MINICONDA_VERSION=${MINICONDA_VERSION} \
    --build-arg IBM_ART_VERSION=${IBM_ART_VERSION} \
    --build-arg MLFLOW_VERSION=${MLFLOW_VERSION} \
    --build-arg PREFECT_VERSION=${PREFECT_VERSION} \
    --build-arg PYTHON_VERSION=${PYTHON_VERSION} \
    --build-arg PYTORCH_CUDA_VERSION=${PYTORCH_CUDA_VERSION} \
    --build-arg PYTORCH_MAJOR_MINOR_VERSION=${PYTORCH_MAJOR_MINOR_VERSION} \
    --build-arg PYTORCH_TORCHAUDIO_VERSION=${PYTORCH_TORCHAUDIO_VERSION} \
    --build-arg PYTORCH_TORCHVISION_VERSION=${PYTORCH_TORCHVISION_VERSION} \
    --build-arg PYTORCH_VERSION=${PYTORCH_VERSION} \
    --build-arg SKLEARN_VERSION=${SKLEARN_VERSION} \
    --build-arg TENSORFLOW_VERSION=${TENSORFLOW_VERSION} \
    --build-arg PYTORCH_NVIDIA_CUDA_VERSION=${PYTORCH_NVIDIA_CUDA_VERSION} \
    --build-arg TENSORFLOW_NVIDIA_CUDA_VERSION=${TENSORFLOW_NVIDIA_CUDA_VERSION} \
    --label "maintainer=NCCoE Artificial Intelligence Team <dioptra@nist.gov>, James Glasbrenner <jglasbrenner@mitre.org>" \
    --label "org.opencontainers.image.title=${PROJECT_COMPONENT}" \
    --label "org.opencontainers.image.description=Provides the ${PROJECT_COMPONENT} microservice within the Dioptra architecture." \
    --label "org.opencontainers.image.authors=NCCoE Artificial Intelligence Team <dioptra@nist.gov>, James Glasbrenner <jglasbrenner@mitre.org>, Cory Miniter <jminiter@mitre.org>, Howard Huang <hhuang@mitre.org>, Julian Sexton <jtsexton@mitre.org>, Paul Rowe <prowe@mitre.org>" \
    --label "org.opencontainers.image.vendor=National Institute of Standards and Technology" \
    --label "org.opencontainers.image.url=https://github.com/usnistgov/dioptra" \
    --label "org.opencontainers.image.source=https://github.com/usnistgov/dioptra" \
    --label "org.opencontainers.image.documentation=https://pages.nist.gov/dioptra" \
    --label "org.opencontainers.image.version=dev" \
    --label "org.opencontainers.image.created=${CREATED_DATE}" \
    --label "org.opencontainers.image.revision=${REVISION}" \
    --label "org.opencontainers.image.licenses=NIST-PD OR CC-BY-4.0" \
    ${BUILD_ARGS} \
    ${BUILD_CONTEXT} ||
    exit 1
fi
