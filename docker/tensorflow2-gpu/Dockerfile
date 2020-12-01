
ARG PROJECT_VERSION
ARG PROJECT_BUILD_NUMBER

FROM securing-ai/sklearn:${PROJECT_VERSION}-${PROJECT_BUILD_NUMBER}

ARG TENSORFLOW2_VERSION
ARG TENSORFLOW2_BUILD=h0d30ee6_0

RUN echo "===> Installing Tensorflow (GPU) environment...."; \
    ${CONDA_DIR}/condabin/conda install -n base -q -y \
    tensorflow-gpu=${TENSORFLOW2_VERSION}=${TENSORFLOW2_BUILD} && \
    echo "===> Cleaning/pruning directories...." && \
    find ${CONDA_DIR} -follow -type f -name '*.a' -delete && \
    find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete && \
    ${CONDA_DIR}/condabin/conda clean -afy && \
    rm -rf /home/${AI_USER}/.cache/yarn && \
    echo "===> Fixing directory permissions...." && \
    fix-permissions.sh ${CONDA_DIR} ${AI_WORKDIR} /home/${AI_USER}

ARG PROJECT_PREFIX
ARG PROJECT_VERSION

COPY dist/mitre_securing_ai-${PROJECT_VERSION}-py3-none-any.whl /etc/${PROJECT_PREFIX}/docker/mitre_securing_ai-${PROJECT_VERSION}-py3-none-any.whl

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

ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility

ARG MAINTAINER="James Glasbrenner <jglasbrenner@mitre.org>"
ARG PROJECT_COMPONENT

LABEL securingai.docker.project.component=${PROJECT_COMPONENT}
LABEL securingai.docker.project.component.maintainer=${MAINTAINER}
