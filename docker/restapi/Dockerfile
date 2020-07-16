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

ARG PROJECT_VERSION
ARG PROJECT_BUILD_NUMBER

FROM securing-ai/miniconda-base:${PROJECT_VERSION}-${PROJECT_BUILD_NUMBER}

ARG MLFLOW_VERSION

ARG ALEMBIC_VERSION=1.4.2
ARG BOTO3_VERSION=1.14.11
ARG CLICK_VERSION=7.1.2
ARG CLOUDPICKLE_VERSION=1.4.1
ARG CYTHON_VERSION=0.29.20
ARG DATABRICKS_CLI_VERSION=0.11.0
ARG DOCKER_PY_VERSION=4.2.1
ARG ENTRYPOINTS_VERSION=0.3
ARG FLASK_ACCEPTS_VERSION=0.17.3
ARG FLASK_INJECTOR_VERSION=0.12.3
ARG FLASK_RESTX_VERSION=0.2.0
ARG FLASK_VERSION=1.1.2
ARG GITPYTHON_VERSION=3.1.1
ARG GORILLA_VERSION=0.3.0
ARG GUNICORN_VERSION=20.0.4
ARG JINJA2_VERSION=2.11.2
ARG MARSHMALLOW_VERSION=3.6.1
ARG NOMKL=3.0
ARG NUMPY_VERSION=1.18.5
ARG PANDAS_VERSION=1.0.5
ARG PILLOW_VERSION=7.1.2
ARG PROMETHEUS_FLASK_EXPORTER_VERSION=0.13.0
ARG PROTOBUF_VERSION=3.12.3
ARG PSYCOPG2_VERSION=2.8.4
ARG PYARROW=0.17.1
ARG PYTHON_DATEUTIL_VERSION=2.8.1
ARG PYTHON_JSON_LOGGER_VERSION=0.1.11
ARG PYTZ_VERSION=2020.1
ARG PYYAML_VERSION=5.3.1
ARG PYZMQ_VERSION=18.1.1
ARG QUERYSTRING_PARSER_VERSION=1.2.4
ARG REQUESTS_VERSION=2.24.0
ARG SCIPY_VERSION=1.4.1
ARG SIMPLEJSON_VERSION=3.17.0
ARG SIX_VERSION=1.15.0
ARG SQLALCHEMY_VERSION=1.3.13
ARG SQLPARSE_VERSION=0.3.1
ARG STRUCTLOG_VERSION=20.1.0
ARG TYPING_EXTENSIONS_VERSION=3.7.4.2
ARG UWSGI_VERSION=2.0.18
ARG WERKZEUG_VERSION=1.0.1

RUN echo "===> Installing dependencies into base conda environment...." && \
    echo "===> Installing dependencies using conda (defaults channel)...." && \
    ${CONDA_DIR}/condabin/conda install -n base -q -y \
    alembic=${ALEMBIC_VERSION} \
    click=${CLICK_VERSION} \
    cloudpickle=${CLOUDPICKLE_VERSION} \
    cython=${CYTHON_VERSION} \
    docker-py=${DOCKER_PY_VERSION} \
    entrypoints=${ENTRYPOINTS_VERSION} \
    gitpython=${GITPYTHON_VERSION} \
    gunicorn=${GUNICORN_VERSION} \
    jinja2=${JINJA2_VERSION} \
    nomkl=${NOMKL} \
    numpy=${NUMPY_VERSION} \
    pandas=${PANDAS_VERSION} \
    pillow=${PILLOW_VERSION} \
    protobuf=${PROTOBUF_VERSION} \
    psycopg2=${PSYCOPG2_VERSION} \
    python-dateutil=${PYTHON_DATEUTIL_VERSION} \
    pytz=${PYTZ_VERSION} \
    pyyaml=${PYYAML_VERSION} \
    pyzmq=${PYZMQ_VERSION} \
    requests=${REQUESTS_VERSION} \
    scipy=${SCIPY_VERSION} \
    simplejson=${SIMPLEJSON_VERSION} \
    six=${SIX_VERSION} \
    sqlalchemy=${SQLALCHEMY_VERSION} \
    sqlparse=${SQLPARSE_VERSION} \
    werkzeug=${WERKZEUG_VERSION} && \
    echo "===> Installing uWSGI using conda (conda-forge channel)...." && \
    ${CONDA_DIR}/condabin/conda install -n base -c defaults -c conda-forge -q -y \
    uwsgi=${UWSGI_VERSION} && \
    echo "===> Installing dependencies using pip...." && \
    ${CONDA_DIR}/condabin/conda run -n base \
    pip install --no-cache-dir \
    boto3==${BOTO3_VERSION} \
    databricks-cli==${DATABRICKS_CLI_VERSION} \
    flask-accepts==${FLASK_ACCEPTS_VERSION} \
    Flask-Injector==${FLASK_INJECTOR_VERSION} \
    flask-restx==${FLASK_RESTX_VERSION} \
    Flask==${FLASK_VERSION} \
    gorilla==${GORILLA_VERSION} \
    marshmallow==${MARSHMALLOW_VERSION} \
    mlflow==${MLFLOW_VERSION} \
    prometheus-flask-exporter==${PROMETHEUS_FLASK_EXPORTER_VERSION} \
    pyarrow==${PYARROW} \
    python-json-logger==${PYTHON_JSON_LOGGER_VERSION} \
    querystring-parser==${QUERYSTRING_PARSER_VERSION} \
    structlog==${STRUCTLOG_VERSION} \
    typing-extensions==${TYPING_EXTENSIONS_VERSION} && \
    echo "===> Cleaning/pruning directories...." && \
    find ${CONDA_DIR} -follow -type f -name '*.a' -delete && \
    find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete && \
    ${CONDA_DIR}/condabin/conda clean -afy && \
    rm -rf /home/${AI_USER}/.cache/yarn && \
    echo "===> Fixing directory permissions...." && \
    fix-permissions.sh ${CONDA_DIR} ${AI_WORKDIR} /home/${AI_USER}

ARG PROJECT_COMPONENT
ARG PROJECT_PREFIX

COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/entrypoint-restapi.sh /etc/${PROJECT_PREFIX}/docker/entrypoint-restapi.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/secure-container.sh /etc/${PROJECT_PREFIX}/docker/secure-container.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/uwsgi.ini /etc/${PROJECT_PREFIX}/docker/uwsgi.ini
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/wsgi.py /etc/${PROJECT_PREFIX}/docker/wsgi.py

USER root

RUN mkdir -p /etc/uwsgi && \
    chown -R ${AI_UID}:${AI_GID} /etc/uwsgi && \
    chown ${AI_UID}:${AI_GID} /etc/${PROJECT_PREFIX}/docker/wsgi.py && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/entrypoint-restapi.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/secure-container.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/entrypoint-restapi.sh /usr/local/bin/entrypoint.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/secure-container.sh /usr/local/bin/secure-container.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/uwsgi.ini /etc/uwsgi/uwsgi.ini && \
    ln -s /etc/${PROJECT_PREFIX}/docker/wsgi.py ${AI_WORKDIR}/wsgi.py

USER ${AI_UID}

ARG PROJECT_VERSION

COPY build/dist/mitre_securing_ai-${PROJECT_VERSION}-py3-none-any.whl /etc/${PROJECT_PREFIX}/docker/mitre_securing_ai-${PROJECT_VERSION}-py3-none-any.whl

RUN echo "===> Installing Securing AI code module...." && \
    ${CONDA_DIR}/condabin/conda run -n base \
    pip install --no-cache-dir --no-deps \
    /etc/${PROJECT_PREFIX}/docker/mitre_securing_ai-${PROJECT_VERSION}-py3-none-any.whl && \
    echo "===> Cleaning/pruning directories...." && \
    find ${CONDA_DIR} -follow -type f -name '*.a' -delete && \
    find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete && \
    ${CONDA_DIR}/condabin/conda clean -afy && \
    rm -rf /home/${AI_USER}/.cache/yarn && \
    echo "===> Fixing directory permissions...." && \
    fix-permissions.sh ${CONDA_DIR} ${AI_WORKDIR} /home/${AI_USER}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]

ARG MAINTAINER="James Glasbrenner <jglasbrenner@mitre.org>"

LABEL securingai.docker.project.component=${PROJECT_COMPONENT}
LABEL securingai.docker.project.component.maintainer=${MAINTAINER}
