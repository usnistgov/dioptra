# Script adapted from the work https://github.com/jupyter/docker-stacks/blob/6bf5922f5a511b4ff28f23783a716df75b8b8d4b/base-notebook/Dockerfile.
# See copyright below.
#
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# Neither the name of the Jupyter Development Team nor the names of its
# contributors may be used to endorse or promote products derived from this
# software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

ARG OS_NAME=ubuntu
ARG OS_VERSION
ARG OS_BUILD_NUMBER

FROM ${OS_NAME}:${OS_VERSION}-${OS_BUILD_NUMBER}

USER root

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV LANGUAGE C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get update && \
    echo "===> Installing ca-certificates curl gosu nginx wget...." && \
    apt-get install -yq --no-install-recommends \
    ca-certificates \
    curl \
    gosu \
    nginx \
    wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# The MITRE certs are necessary to install in order for wget to work
ADD http://pki.mitre.org/MITRE%20BA%20ROOT.crt /usr/local/share/ca-certificates/MITRE-BA-ROOT.crt
ADD http://pki.mitre.org/MITRE%20BA%20NPE%20CA-3%281%29.crt /usr/local/share/ca-certificates/MITRE-BA-NPE-CA-3-1.crt
ADD http://pki.mitre.org/MITRE-chain.txt /usr/local/share/ca-certificates/MITRE-chain.pem

RUN cat /etc/ssl/certs/ca-certificates.crt /usr/local/share/ca-certificates/MITRE-chain.pem >/etc/ssl/certs/ca-certificates-plus-mitre.pem && \
    /usr/sbin/update-ca-certificates

ENV AWS_CA_BUNDLE /etc/ssl/certs/ca-certificates-plus-mitre.pem
ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates-plus-mitre.pem
ENV NODE_EXTRA_CA_CERTS /etc/ssl/certs/ca-certificates-plus-mitre.pem
ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates-plus-mitre.pem
ENV SSL_CERT_FILE /etc/ssl/certs/ca-certificates-plus-mitre.pem

ARG AI_USER=securingai
ARG AI_UID=39000
ARG AI_GID=100
ARG AI_WORKDIR=/work
ARG PROJECT_COMPONENT
ARG PROJECT_PREFIX

COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/entrypoint-nginx.sh /etc/${PROJECT_PREFIX}/docker/entrypoint-nginx.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/fix-permissions.sh /etc/${PROJECT_PREFIX}/docker/fix-permissions.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/secure-container.sh /etc/${PROJECT_PREFIX}/docker/secure-container.sh

RUN chmod 0755 /etc/${PROJECT_PREFIX}/docker/fix-permissions.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/entrypoint-nginx.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/secure-container.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/fix-permissions.sh /usr/local/bin/fix-permissions.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/entrypoint-nginx.sh /usr/local/bin/entrypoint.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/secure-container.sh /usr/local/bin/secure-container.sh && \
    sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/skel/.bashrc && \
    useradd -u ${AI_UID} -N -m -s /bin/bash -c "Securing AI Lab user" ${AI_USER} && \
    chown -R ${AI_UID}:${AI_GID} /home/${AI_USER} && \
    chmod g+w /etc/passwd && \
    fix-permissions.sh /home/${AI_USER}

COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/nginx.conf /etc/${PROJECT_PREFIX}/docker/nginx.conf

RUN mkdir -p /etc/nginx/conf.d && \
    mkdir -p /var/cache/nginx && \
    mkdir -p /var/log/nginx && \
    touch /var/run/nginx.pid && \
    rm /etc/nginx/nginx.conf && \
    chown -R ${AI_UID}:${AI_GID} /etc/nginx/conf.d && \
    chown -R ${AI_UID}:${AI_GID} /var/cache/nginx && \
    chown -R ${AI_UID}:${AI_GID} /var/log/nginx && \
    chown -R ${AI_UID}:${AI_GID} /var/run/nginx.pid && \
    ln -s /etc/${PROJECT_PREFIX}/docker/nginx.conf /etc/nginx/nginx.conf

USER ${AI_UID}

ENV AI_USER ${AI_USER}
ENV AI_UID ${AI_UID}
ENV AI_GID ${AI_GID}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

ARG OS_NAME=ubuntu
ARG OS_VERSION
ARG OS_VERSION_NUMBER
ARG OS_BUILD_NUMBER
ARG MAINTAINER="James Glasbrenner <jglasbrenner@mitre.org>"
ARG PROJECT_VERSION
ARG PROJECT_BUILD_NUMBER

LABEL securingai.docker=true
LABEL securingai.docker.os.name=${OS_NAME}
LABEL securingai.docker.os.version.name=${OS_VERSION}
LABEL securingai.docker.os.version.number=${OS_VERSION_NUMBER}
LABEL securingai.docker.os.build=${OS_BUILD_NUMBER}
LABEL securingai.docker.project.component=${PROJECT_COMPONENT}
LABEL securingai.docker.project.component.maintainer=${MAINTAINER}
LABEL securingai.docker.project.version=${PROJECT_VERSION}
LABEL securingai.docker.project.build=${PROJECT_BUILD_NUMBER}
