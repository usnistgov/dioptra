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
FROM ubuntu:focal

USER root

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV LANGUAGE C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get update && \
    echo "===> Upgrade existing packages...." && \
    apt-get -y upgrade && \
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
ADD http://pki.mitre.org/ZScaler_Root.crt /usr/local/share/ca-certificates/ZScaler_Root.crt

RUN cat /etc/ssl/certs/ca-certificates.crt /usr/local/share/ca-certificates/MITRE-chain.pem /usr/local/share/ca-certificates/ZScaler_Root.crt >/etc/ssl/certs/ca-certificates-plus-mitre.pem && \
    /usr/sbin/update-ca-certificates

ENV AWS_CA_BUNDLE /etc/ssl/certs/ca-certificates-plus-mitre.pem
ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates-plus-mitre.pem
ENV NODE_EXTRA_CA_CERTS /etc/ssl/certs/ca-certificates-plus-mitre.pem
ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates-plus-mitre.pem
ENV SSL_CERT_FILE /etc/ssl/certs/ca-certificates-plus-mitre.pem

ARG PROJECT_COMPONENT
ARG PROJECT_PREFIX

COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/entrypoint-nginx.sh /etc/${PROJECT_PREFIX}/docker/entrypoint-nginx.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/init-copy.sh /etc/${PROJECT_PREFIX}/docker/init-copy.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/init-git-clone.sh /etc/${PROJECT_PREFIX}/docker/init-git-clone.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/init-set-permissions.sh /etc/${PROJECT_PREFIX}/docker/init-set-permissions.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/secure-container.sh /etc/${PROJECT_PREFIX}/docker/secure-container.sh

ARG DIOPTRA_USER=dioptra
ARG DIOPTRA_UID=39000
ARG DIOPTRA_GID=100

RUN chmod 0755 /etc/${PROJECT_PREFIX}/docker/entrypoint-nginx.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/init-copy.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/init-git-clone.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/init-set-permissions.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/secure-container.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/entrypoint-nginx.sh /usr/local/bin/entrypoint.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/init-copy.sh /usr/local/bin/init-copy.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/init-git-clone.sh /usr/local/bin/init-git-clone.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/init-set-permissions.sh /usr/local/bin/init-set-permissions.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/secure-container.sh /usr/local/bin/secure-container.sh && \
    sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/skel/.bashrc && \
    useradd -u ${DIOPTRA_UID} -N -M -s /bin/bash -c "Dioptra user" ${DIOPTRA_USER} && \
    chmod g+w /etc/passwd

COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/nginx.conf /etc/${PROJECT_PREFIX}/docker/nginx.conf
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/default.conf /etc/${PROJECT_PREFIX}/docker/default.conf

RUN mkdir -p /etc/nginx/conf.d && \
    mkdir -p /var/cache/nginx && \
    mkdir -p /var/lib/nginx && \
    mkdir -p /var/log/nginx && \
    rm /etc/nginx/nginx.conf && \
    chmod 0644 /etc/${PROJECT_PREFIX}/docker/nginx.conf && \
    chmod 0644 /etc/${PROJECT_PREFIX}/docker/default.conf && \
    chmod 0755 /etc/nginx/conf.d && \
    chmod 0755 /var/cache/nginx && \
    chmod 0755 /var/lib/nginx && \
    chmod 0755 /var/log/nginx && \
    chown ${DIOPTRA_UID}:${DIOPTRA_GID} /etc/${PROJECT_PREFIX}/docker/nginx.conf && \
    chown ${DIOPTRA_UID}:${DIOPTRA_GID} /etc/${PROJECT_PREFIX}/docker/default.conf && \
    chown -R ${DIOPTRA_UID}:${DIOPTRA_GID} /etc/nginx/conf.d && \
    chown -R ${DIOPTRA_UID}:${DIOPTRA_GID} /var/cache/nginx && \
    chown -R ${DIOPTRA_UID}:${DIOPTRA_GID} /var/lib/nginx && \
    chown -R ${DIOPTRA_UID}:${DIOPTRA_GID} /var/log/nginx && \
    ln -s /etc/${PROJECT_PREFIX}/docker/nginx.conf /etc/nginx/nginx.conf && \
    ln -s /etc/${PROJECT_PREFIX}/docker/default.conf /etc/nginx/conf.d/default.conf

USER ${DIOPTRA_UID}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

ENV DIOPTRA_USER ${DIOPTRA_USER}
ENV DIOPTRA_UID ${DIOPTRA_UID}
ENV DIOPTRA_GID ${DIOPTRA_GID}
