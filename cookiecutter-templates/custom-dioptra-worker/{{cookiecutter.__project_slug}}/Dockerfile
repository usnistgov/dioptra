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

######################################################################################################
# Base images
######################################################################################################

# -- Base image --------------------------------------------------------------------------------------

FROM ghcr.io/astral-sh/uv:debian AS base

USER root

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8
ENV LC_ALL=C.UTF-8

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -yq --no-install-recommends \
    netcat-traditional && \
    # Cleanup
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# -- Base image (includes extra CA certificates) -----------------------------------------------------

FROM base AS certs-base

COPY --chown=root:root ca-certificates /ca-certificates

RUN chmod 0644 /ca-certificates/* && \
    cp /ca-certificates/*.crt /usr/local/share/ca-certificates 2>/dev/null || true && \
    /usr/sbin/update-ca-certificates

ENV AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# -- Base image (argbash) ----------------------------------------------------------------------------

FROM certs-base AS argbash-base

ARG ARGBASH_VERSION={{ cookiecutter.__argbash_version }}

RUN cd /tmp && \
    curl -L -o "/tmp/argbash.tar.gz" "https://github.com/matejak/argbash/archive/refs/tags/${ARGBASH_VERSION}.tar.gz" && \
    tar xf /tmp/argbash.tar.gz && \
    cd /tmp/argbash-${ARGBASH_VERSION}/resources && \
    make install PREFIX=/usr/local && \
    cd / && \
    rm -rf /tmp/argbash.tar.gz /tmp/argbash-${ARGBASH_VERSION}

######################################################################################################
# Build
######################################################################################################

# -- Build: render bash script templates ------------------------------------------------------

FROM argbash-base AS shellscripts

COPY --chown=root:root --chmod=0755 shellscripts/entrypoint-worker.m4 /templates/entrypoint-worker.m4
COPY --chown=root:root --chmod=0755 shellscripts/healthcheck-worker.m4 /templates/healthcheck-worker.m4

COPY --chown=root:root --chmod=0755 shellscripts/wait-for-it.sh /shellscripts/wait-for-it.sh

RUN mkdir -p /shellscripts && \
    /usr/local/bin/argbash /templates/entrypoint-worker.m4 -o /shellscripts/entrypoint-worker.sh && \
    /usr/local/bin/argbash /templates/healthcheck-worker.m4 -o /shellscripts/healthcheck-worker.sh

# -- Build: create virtual environment ---------------------------------------------------------------

FROM certs-base AS build-venv

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_CACHE_DIR=/root/.cache/uv/python
ENV UV_PYTHON_INSTALL_DIR=/opt/uv/python

COPY --chown=root:root requirements.txt /code/requirements.txt

WORKDIR /code

# Install Python
ARG PYTHON_VERSION={{ cookiecutter.__python_version }}
RUN --mount=type=cache,target=/root/.cache/uv \
    umask 0002 && \
    uv python install ${PYTHON_VERSION}

ENV PATH=/opt/uv/python${PATH:+:${PATH}}

# Create the Python virtual environment
ARG VIRTUAL_ENV=/opt/venv
RUN --mount=type=cache,target=/root/.cache/uv \
    umask 0002 && \
    uv venv --python ${PYTHON_VERSION} ${VIRTUAL_ENV}

ENV PATH=${VIRTUAL_ENV}/bin${PATH:+:${PATH}}
ENV VIRTUAL_ENV=${VIRTUAL_ENV}

# Install packages from requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv \
    umask 0002 && \
    uv pip install -r /code/requirements.txt

######################################################################################################
# Final image
######################################################################################################

FROM base AS final

ARG DIOPTRA_USER=dioptra
ARG DIOPTRA_UID=39000
ARG DIOPTRA_GID=100
ARG DIOPTRA_WORKDIR=/work
ARG VIRTUAL_ENV=/opt/venv

RUN umask 0022 && \
    sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/skel/.bashrc && \
    useradd -u ${DIOPTRA_UID} -N -m -s /bin/bash -c "Dioptra user" ${DIOPTRA_USER} && \
    mkdir -p /home/${DIOPTRA_USER}/.aws/config && \
    mkdir -p ${DIOPTRA_WORKDIR} && \
    chown -R ${DIOPTRA_UID}:${DIOPTRA_GID} /home/${DIOPTRA_USER} && \
    chown -R ${DIOPTRA_UID}:${DIOPTRA_GID} ${DIOPTRA_WORKDIR}

COPY --from=shellscripts --chown=root:root --chmod=0755 /shellscripts/entrypoint-worker.sh /usr/local/bin/entrypoint.sh
COPY --from=shellscripts --chown=root:root --chmod=0755 /shellscripts/healthcheck-worker.sh /usr/local/bin/healthcheck.sh
COPY --from=shellscripts --chown=root:root --chmod=0755 /shellscripts/wait-for-it.sh /usr/local/bin/wait-for-it.sh
COPY --chown=${DIOPTRA_UID}:${DIOPTRA_GID} --chmod=0644 configs/aws-config /home/${DIOPTRA_USER}/.aws/config/aws-config

COPY --from=build-venv --chown=${DIOPTRA_UID}:${DIOPTRA_GID} /opt/uv /opt/uv
COPY --from=build-venv --chown=${DIOPTRA_UID}:${DIOPTRA_GID} ${VIRTUAL_ENV} ${VIRTUAL_ENV}

ENV DIOPTRA_USER=${DIOPTRA_USER}
ENV DIOPTRA_UID=${DIOPTRA_UID}
ENV DIOPTRA_GID=${DIOPTRA_GID}
ENV DIOPTRA_RESTAPI_ENV=prod
ENV DIOPTRA_WORKDIR=${DIOPTRA_WORKDIR}
ENV PATH=${VIRTUAL_ENV}/bin:/opt/uv/python${PATH:+:${PATH}}
ENV VIRTUAL_ENV=${VIRTUAL_ENV}

USER ${DIOPTRA_UID}
WORKDIR ${DIOPTRA_WORKDIR}
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
VOLUME ["/etc/ssl", "/usr/local/share/ca-certificates"]
