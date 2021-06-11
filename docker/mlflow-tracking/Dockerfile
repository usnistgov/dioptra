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
#
# Part of this script is adapted from the work
# https://github.com/jupyter/docker-stacks/blob/6bf5922f5a511b4ff28f23783a716df75b8b8d4b/base-notebook/Dockerfile.
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
    echo "===> Installing ca-certificates curl git gosu libbz2-1.0 liblz4-1 liblzma5 libsnappy1v5 libzstd1 unzip wget zlib1g...." && \
    apt-get install -yq --no-install-recommends \
    ca-certificates \
    curl \
    git \
    gosu \
    libbz2-1.0 \
    liblz4-1 \
    liblzma5 \
    libsnappy1v5 \
    libzstd1 \
    unzip \
    wget \
    zlib1g && \
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

ARG AWSCLI_DOWNLOAD_URL=https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip
ARG AWSCLI_INSTALL_DIR=/opt/aws-cli
ARG AWSCLI_BIN_DIR=/usr/local/bin

RUN cd /tmp && \
    wget -qO /tmp/awscliv2.zip ${AWSCLI_DOWNLOAD_URL} && \
    unzip awscliv2.zip && \
    rm /tmp/awscliv2.zip && \
    ./aws/install --install-dir ${AWSCLI_INSTALL_DIR} --bin-dir ${AWSCLI_BIN_DIR} && \
    rm -rf /tmp/aws

ARG AI_USER=securingai
ARG AI_UID=39000
ARG AI_GID=100
ARG AI_WORKDIR=/work
ARG CONDA_DIR=/opt/conda
ARG PROJECT_COMPONENT
ARG PROJECT_PREFIX

COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/fix-permissions.sh /etc/${PROJECT_PREFIX}/docker/fix-permissions.sh

RUN chmod 0755 /etc/${PROJECT_PREFIX}/docker/fix-permissions.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/fix-permissions.sh /usr/local/bin/fix-permissions.sh

RUN sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/skel/.bashrc

RUN useradd -u ${AI_UID} -N -m -s /bin/bash -c "Securing AI Testbed user" ${AI_USER} && \
    mkdir -p /home/${AI_USER}/.aws/cli && \
    mkdir -p /home/${AI_USER}/.conda && \
    mkdir -p ${CONDA_DIR} && \
    mkdir -p ${AI_WORKDIR} && \
    chown -R ${AI_UID}:${AI_GID} /home/${AI_USER} && \
    chown -R ${AI_UID}:${AI_GID} ${CONDA_DIR} && \
    chown -R ${AI_UID}:${AI_GID} ${AI_WORKDIR} && \
    chmod g+w /etc/passwd && \
    fix-permissions.sh /home/${AI_USER} ${AI_WORKDIR} ${CONDA_DIR}

COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/aws-config /etc/${PROJECT_PREFIX}/docker/aws-config
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/dot-condarc /etc/${PROJECT_PREFIX}/docker/dot-condarc

RUN chown ${AI_UID}:${AI_GID} /etc/${PROJECT_PREFIX}/docker/dot-condarc && \
    chown ${AI_UID}:${AI_GID} /etc/${PROJECT_PREFIX}/docker/aws-config && \
    chmod 0644 /etc/${PROJECT_PREFIX}/docker/aws-config && \
    chmod 0644 /etc/${PROJECT_PREFIX}/docker/dot-condarc && \
    ln -s /etc/${PROJECT_PREFIX}/docker/aws-config /home/${AI_USER}/.aws/config && \
    ln -s /etc/${PROJECT_PREFIX}/docker/dot-condarc /home/${AI_USER}/.condarc && \
    fix-permissions.sh /home/${AI_USER} ${AI_WORKDIR} ${CONDA_DIR}

USER ${AI_UID}

ARG MINICONDA_VERSION
ARG MINICONDA3_PREFIX=Miniconda3-py37_
ARG PYTHON_VERSION=default

RUN echo "===> Installing Miniconda3 version ${MINICONDA_VERSION} to ${CONDA_DIR}...." && \
    cd /tmp && \
    wget -qO "/tmp/${MINICONDA3_PREFIX}${MINICONDA_VERSION}-Linux-x86_64.sh" "https://repo.continuum.io/miniconda/${MINICONDA3_PREFIX}${MINICONDA_VERSION}-Linux-x86_64.sh" && \
    bash ${MINICONDA3_PREFIX}${MINICONDA_VERSION}-Linux-x86_64.sh -f -b -p ${CONDA_DIR} && \
    rm ${MINICONDA3_PREFIX}${MINICONDA_VERSION}-Linux-x86_64.sh && \
    if [ ! ${PYTHON_VERSION} = 'default' ]; then ${CONDA_DIR}/condabin/conda install -y python=$PYTHON_VERSION; fi && \
    ${CONDA_DIR}/condabin/conda install -q -y conda && \
    ${CONDA_DIR}/condabin/conda install -q -y pip && \
    ${CONDA_DIR}/condabin/conda update -q -y --all && \
    ${CONDA_DIR}/condabin/conda list python | grep '^python ' | tr -s ' ' | cut -d '.' -f 1,2 | sed 's/$/.*/' >> ${CONDA_DIR}/conda-meta/pinned && \
    find ${CONDA_DIR} -follow -type f -name '*.a' -delete && \
    find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete && \
    ${CONDA_DIR}/condabin/conda clean -a -f -y && \
    rm -rf /home/${AI_USER}/.cache/pip && \
    rm -rf /home/${AI_USER}/.cache/yarn && \
    fix-permissions.sh /home/${AI_USER} ${AI_WORKDIR} ${CONDA_DIR}

COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/environment-${PROJECT_COMPONENT}.yml /etc/${PROJECT_PREFIX}/docker/environment-${PROJECT_COMPONENT}.yml

RUN echo "===> Installing base dependencies in conda environment of ${PROJECT_COMPONENT} image...." && \
    cp /etc/${PROJECT_PREFIX}/docker/environment-${PROJECT_COMPONENT}.yml /tmp/environment-${PROJECT_COMPONENT}.yml && \
    ${CONDA_DIR}/condabin/conda env create --file /tmp/environment-${PROJECT_COMPONENT}.yml && \
    echo "===> Cleaning/pruning directories...." && \
    rm -f /tmp/environment-${PROJECT_COMPONENT}.yml && \
    find ${CONDA_DIR} -follow -type f -name '*.a' -delete && \
    find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete && \
    ${CONDA_DIR}/condabin/conda clean -afy && \
    rm -rf /home/${AI_USER}/.cache/pip && \
    rm -rf /home/${AI_USER}/.cache/yarn && \
    echo "===> Fixing directory permissions...." && \
    fix-permissions.sh ${CONDA_DIR} ${AI_WORKDIR} /home/${AI_USER}

USER root

COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/bash.bashrc /etc/${PROJECT_PREFIX}/docker/bash.bashrc
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/entrypoint-${PROJECT_COMPONENT}.sh /etc/${PROJECT_PREFIX}/docker/entrypoint-${PROJECT_COMPONENT}.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/parse-uri.sh /etc/${PROJECT_PREFIX}/docker/parse-uri.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/s3-cp.sh /etc/${PROJECT_PREFIX}/docker/s3-cp.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/s3-mb.sh /etc/${PROJECT_PREFIX}/docker/s3-mb.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/s3-sync.sh /etc/${PROJECT_PREFIX}/docker/s3-sync.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/unpack-archive.sh /etc/${PROJECT_PREFIX}/docker/unpack-archive.sh

RUN chmod 0644 /etc/${PROJECT_PREFIX}/docker/bash.bashrc && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/entrypoint-${PROJECT_COMPONENT}.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/parse-uri.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/s3-cp.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/s3-mb.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/s3-sync.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/unpack-archive.sh && \
    rm /etc/bash.bashrc && \
    ln -s /etc/${PROJECT_PREFIX}/docker/bash.bashrc /etc/bash.bashrc && \
    ln -s /etc/${PROJECT_PREFIX}/docker/entrypoint-${PROJECT_COMPONENT}.sh /usr/local/bin/entrypoint.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/parse-uri.sh /usr/local/bin/parse-uri.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/s3-cp.sh /usr/local/bin/s3-cp.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/s3-mb.sh /usr/local/bin/s3-mb.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/s3-sync.sh /usr/local/bin/s3-sync.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/unpack-archive.sh /usr/local/bin/unpack-archive.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh

ENV AI_USER ${AI_USER}
ENV AI_UID ${AI_UID}
ENV AI_GID ${AI_GID}
ENV AI_WORKDIR ${AI_WORKDIR}
ENV CONDA_DIR ${CONDA_DIR}

USER ${AI_UID}
WORKDIR ${AI_WORKDIR}
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

ARG OS_NAME=ubuntu
ARG OS_VERSION
ARG OS_VERSION_NUMBER
ARG OS_BUILD_NUMBER
ARG MAINTAINER="James Glasbrenner <jglasbrenner@mitre.org>"
ARG PROJECT_VERSION

LABEL securingai.docker=true
LABEL securingai.docker.os.name=${OS_NAME}
LABEL securingai.docker.os.version.name=${OS_VERSION}
LABEL securingai.docker.os.version.number=${OS_VERSION_NUMBER}
LABEL securingai.docker.os.build=${OS_BUILD_NUMBER}
LABEL securingai.docker.project.component=${PROJECT_COMPONENT}
LABEL securingai.docker.project.component.maintainer=${MAINTAINER}
LABEL securingai.docker.project.version=${PROJECT_VERSION}
