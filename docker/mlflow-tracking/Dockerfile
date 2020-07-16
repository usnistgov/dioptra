
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
ARG FLASK_VERSION=1.1.2
ARG GITPYTHON_VERSION=3.1.1
ARG GORILLA_VERSION=0.3.0
ARG GUNICORN_VERSION=20.0.4
ARG JINJA2_VERSION=2.11.2
ARG NOMKL=3.0
ARG NUMPY_VERSION=1.18.5
ARG PANDAS_VERSION=1.0.5
ARG PROMETHEUS_FLASK_EXPORTER_VERSION=0.13.0
ARG PROTOBUF_VERSION=3.12.3
ARG PSYCOPG2_VERSION=2.8.4
ARG PYTHON_DATEUTIL_VERSION=2.8.1
ARG PYTZ_VERSION=2020.1
ARG PYYAML_VERSION=5.3.1
ARG QUERYSTRING_PARSER_VERSION=1.2.4
ARG REQUESTS_VERSION=2.24.0
ARG SCIPY_VERSION=1.4.1
ARG SIMPLEJSON_VERSION=3.17.0
ARG SIX_VERSION=1.15.0
ARG SQLALCHEMY_VERSION=1.3.13
ARG SQLPARSE_VERSION=0.3.1
ARG WERKZEUG_VERSION=1.0.1

RUN echo "===> Installing dependencies using conda (defaults channel)...." && \
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
    protobuf=${PROTOBUF_VERSION} \
    psycopg2=${PSYCOPG2_VERSION} \
    python-dateutil=${PYTHON_DATEUTIL_VERSION} \
    pytz=${PYTZ_VERSION} \
    pyyaml=${PYYAML_VERSION} \
    requests=${REQUESTS_VERSION} \
    scipy=${SCIPY_VERSION} \
    simplejson=${SIMPLEJSON_VERSION} \
    six=${SIX_VERSION} \
    sqlalchemy=${SQLALCHEMY_VERSION} \
    sqlparse=${SQLPARSE_VERSION} \
    werkzeug=${WERKZEUG_VERSION} && \
    echo "===> Installing dependencies using pip...." && \
    ${CONDA_DIR}/condabin/conda run -n base \
    pip install --no-cache-dir \
    boto3==${BOTO3_VERSION} \
    databricks-cli==${DATABRICKS_CLI_VERSION} \
    Flask==${FLASK_VERSION} \
    gorilla==${GORILLA_VERSION} \
    mlflow==${MLFLOW_VERSION} \
    prometheus-flask-exporter==${PROMETHEUS_FLASK_EXPORTER_VERSION} \
    querystring-parser==${QUERYSTRING_PARSER_VERSION} && \
    echo "===> Cleaning/pruning directories...." && \
    find ${CONDA_DIR} -follow -type f -name '*.a' -delete && \
    find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete && \
    ${CONDA_DIR}/condabin/conda clean -afy && \
    rm -rf /home/${AI_USER}/.cache/yarn && \
    echo "===> Fixing directory permissions...." && \
    fix-permissions.sh ${CONDA_DIR} ${AI_WORKDIR} /home/${AI_USER}

ARG PROJECT_COMPONENT
ARG PROJECT_PREFIX

USER root

COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/s3-mb.sh /etc/${PROJECT_PREFIX}/docker/s3-mb.sh
COPY docker/${PROJECT_COMPONENT}/include/etc/${PROJECT_PREFIX}/docker/entrypoint-mlflow-tracking.sh /etc/${PROJECT_PREFIX}/docker/entrypoint-mlflow-tracking.sh

RUN chmod 0755 /etc/${PROJECT_PREFIX}/docker/entrypoint-mlflow-tracking.sh && \
    chmod 0755 /etc/${PROJECT_PREFIX}/docker/s3-mb.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/entrypoint-mlflow-tracking.sh /usr/local/bin/entrypoint.sh && \
    ln -s /etc/${PROJECT_PREFIX}/docker/s3-mb.sh /usr/local/bin/s3-mb.sh && \
    fix-permissions.sh ${CONDA_DIR} ${AI_WORKDIR} /home/${AI_USER}

USER ${AI_UID}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

ARG MAINTAINER="James Glasbrenner <jglasbrenner@mitre.org>"

LABEL securingai.docker.project.component=${PROJECT_COMPONENT}
LABEL securingai.docker.project.component.maintainer=${MAINTAINER}
