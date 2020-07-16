
FROM postgres:12.3

ARG OS_NAME=debian
ARG OS_VERSION=buster
ARG OS_VERSION_NUMBER=10
ARG MAINTAINER="James Glasbrenner <jglasbrenner@mitre.org>"
ARG PROJECT_COMPONENT
ARG PROJECT_VERSION
ARG PROJECT_BUILD_NUMBER

LABEL securingai.docker=true
LABEL securingai.docker.os.name=${OS_NAME}
LABEL securingai.docker.os.version.name=${OS_VERSION}
LABEL securingai.docker.os.version.number=${OS_VERSION_NUMBER}
LABEL securingai.docker.project.component=${PROJECT_COMPONENT}
LABEL securingai.docker.project.component.maintainer=${MAINTAINER}
LABEL securingai.docker.project.version=${PROJECT_VERSION}
LABEL securingai.docker.project.build=${PROJECT_BUILD_NUMBER}
