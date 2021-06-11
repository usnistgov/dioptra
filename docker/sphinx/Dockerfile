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
ARG SPHINX_VERSION

FROM sphinxdoc/sphinx:${SPHINX_VERSION}

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV LANGUAGE C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -yq --no-install-recommends \
    ca-certificates \
    curl \
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

RUN pip install --no-cache-dir --no-color \
    Flask \
    flask-accepts \
    Flask-JWT-Extended \
    flask-restx \
    Flask-SQLAlchemy \
    Flask-WTF \
    markdown \
    marshmallow \
    multimethod \
    plantuml-markdown \
    pymdown-extensions \
    recommonmark \
    sphinx_togglebutton \
    sphinx-book-theme>=0.0.39 \
    sphinx-copybutton \
    sphinx-panels~=0.5.2 \
    sphinx-rtd-theme \
    sphinxcontrib-openapi \
    SQLAlchemy \
    typing-extensions && \
    find /usr/local -depth \
    \( \
    \( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
    -o \
    \( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
    \) -exec rm -rf '{}' + && \
    rm -rf /tmp/*

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
