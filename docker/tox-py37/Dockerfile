# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
FROM python:3.7-slim-buster

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV LANGUAGE C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -yq --no-install-recommends \
    ca-certificates \
    curl \
    git \
    gosu \
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

RUN /usr/local/bin/python -m pip install --no-cache-dir --no-color --upgrade pip && \
    /usr/local/bin/python -m pip install --no-cache-dir --no-color tox && \
    find /usr/local -depth \
    \( \
    \( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
    -o \
    \( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
    \) -exec rm -rf '{}' +

ARG AI_USER=securingai
ARG AI_UID=39000
ARG AI_GID=100

RUN sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/skel/.bashrc && \
    useradd -u ${AI_UID} -N -m -s /bin/bash ${AI_USER} && \
    mkdir -p /home/${AI_USER}/.local/bin && \
    mkdir -p /home/${AI_USER}/.local/include && \
    mkdir -p /home/${AI_USER}/.local/lib && \
    chown -R ${AI_UID}:${AI_GID} /home/${AI_USER}

USER ${AI_UID}

ENV AI_USER ${AI_USER}
ENV AI_UID ${AI_UID}
ENV AI_GID ${AI_GID}
ENV PATH ${PATH:+${PATH}:}/home/${AI_USER}/.local/bin
ENV CPATH /home/${AI_USER}/.local/include${CPATH:+:${CPATH}}
ENV LIBRARY_PATH /home/${AI_USER}/.local/lib${LIBRARY_PATH:+:${LIBRARY_PATH}}

ARG MAINTAINER="James Glasbrenner <jglasbrenner@mitre.org>"
ARG PROJECT_COMPONENT

LABEL securingai.docker=true
LABEL securingai.docker.os.name=debian
LABEL securingai.docker.os.version.name=buster
LABEL securingai.docker.os.version.number=10
LABEL securingai.docker.project.component=${PROJECT_COMPONENT}
LABEL securingai.docker.project.component.maintainer=${MAINTAINER}
