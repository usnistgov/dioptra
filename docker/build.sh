#!/bin/bash

echo ""
echo "------------- ENV variables --------------------"
echo "DOCKER_NO_CACHE=${DOCKER_NO_CACHE}"
echo "DOCKER_BUILD_TARGET=${DOCKER_BUILD_TARGET}"
echo "DOCKER_BUILDKIT_VALUE=${DOCKER_BUILDKIT_VALUE}"
echo "IMAGE_TAG=${IMAGE_TAG}"
echo ""

prefix=${PROJECT_PREFIX}

echo ""
echo "Building ${prefix}/${PROJECT_COMPONENT}"
echo "=========================================="
echo ""

DOCKERFILE="docker/Dockerfile.${PROJECT_COMPONENT}"
BUILD_CONTEXT="."
BUILD_ARGS="${DOCKER_BUILD_ARGS}"
IMAGE_NAME="${prefix}/${PROJECT_COMPONENT}"
CREATED_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
REVISION="$(git log -1 --pretty=%H)"

if [[ -e ${DOCKERFILE} ]]; then
  DOCKER_BUILDKIT=${DOCKER_BUILDKIT_VALUE} \
    docker build ${DOCKER_NO_CACHE} \
    --tag ${IMAGE_NAME}:${IMAGE_TAG} \
    -f ${DOCKERFILE} \
    --target ${DOCKER_BUILD_TARGET} \
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
