#!/bin/bash

echo ""
echo "------------- ENV variables --------------------"
echo "CORES=${CORES}"
echo "IMAGE_TAG=${IMAGE_TAG}"
echo "CODE_PKG_VERSION=${CODE_PKG_VERSION}"
echo "PROJECT_COMPONENT=${PROJECT_COMPONENT}"
echo "PROJECT_PREFIX=${PROJECT_PREFIX}"
echo "MINICONDA3_PREFIX=${MINICONDA3_PREFIX}"
echo "MINICONDA_VERSION=${MINICONDA_VERSION}"
echo "PYTORCH_VERSION=${PYTORCH_VERSION}"
echo "SPHINX_VERSION=${SPHINX_VERSION}"
echo "TENSORFLOW2_VERSION=${TENSORFLOW2_VERSION}"
echo ""

prefix=${PROJECT_PREFIX}

echo ""
echo "Building ${prefix}/${PROJECT_COMPONENT}"
echo "=========================================="
echo ""

DOCKERFILE="docker/${PROJECT_COMPONENT}/Dockerfile"
BUILD_CONTEXT="."
BUILD_ARGS=""
IMAGE_NAME="${prefix}/${PROJECT_COMPONENT}"
CREATED_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
REVISION="$(git log -1 --pretty=%H)"

if [[ -e ${DOCKERFILE} ]]; then
  docker build \
    --tag ${IMAGE_NAME}:${IMAGE_TAG} \
    -f ${DOCKERFILE} \
    --build-arg CORES=${CORES} \
    --build-arg CODE_PKG_VERSION=${CODE_PKG_VERSION} \
    --build-arg PROJECT_COMPONENT=${PROJECT_COMPONENT} \
    --build-arg PROJECT_PREFIX=${PROJECT_PREFIX} \
    --build-arg MINICONDA3_PREFIX=${MINICONDA3_PREFIX} \
    --build-arg MINICONDA_VERSION=${MINICONDA_VERSION} \
    --build-arg PYTORCH_VERSION=${PYTORCH_VERSION} \
    --build-arg SPHINX_VERSION=${SPHINX_VERSION} \
    --build-arg TENSORFLOW2_VERSION=${TENSORFLOW2_VERSION} \
    --label "maintainer=NCCoE Artificial Intelligence Team <ai-nccoe@nist.gov>, James Glasbrenner <jglasbrenner@mitre.org>" \
    --label "org.opencontainers.image.title=${PROJECT_COMPONENT}" \
    --label "org.opencontainers.image.description=Provides the ${PROJECT_COMPONENT} microservice within the Dioptra architecture." \
    --label "org.opencontainers.image.authors=NCCoE Artificial Intelligence Team <ai-nccoe@nist.gov>, James Glasbrenner <jglasbrenner@mitre.org>, Cory Miniter <jminiter@mitre.org>, Howard Huang <hhuang@mitre.org>, Julian Sexton <jtsexton@mitre.org>, Paul Rowe <prowe@mitre.org>" \
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
