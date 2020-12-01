
ARG PROJECT_VERSION
ARG PROJECT_BUILD_NUMBER

FROM securing-ai/sklearn:${PROJECT_VERSION}-${PROJECT_BUILD_NUMBER}

ARG GOOGLE_AUTH_VERSION=1.23.0
ARG GOOGLE_AUTH_OAUTHLIB_VERSION=0.4.2
ARG GRPCIO_VERSION=1.31.0
ARG PYASN1_VERSION=0.4.8
ARG PYASN1_MODULES_VERSION=0.2.8
ARG PYTORCH_CUDATOOLKIT_VERSION=11.0.221
ARG PYTORCH_LIGHTNING_VERSION=1.1.0
ARG PYTORCH_TORCHVISION_VERSION=0.8.1
ARG TENSORBOARD_VERSION=2.3.0

RUN echo "===> Installing PyTorch (GPU) environment...." && \
    ${CONDA_DIR}/condabin/conda install -n base -c defaults -c pytorch -q -y \
    cudatoolkit=${PYTORCH_CUDATOOLKIT_VERSION} \
    google-auth=${GOOGLE_AUTH_VERSION} \
    google-auth-oauthlib=${GOOGLE_AUTH_OAUTHLIB_VERSION} \
    grpcio=${GRPCIO_VERSION} \
    pyasn1=${PYASN1_VERSION} \
    pyasn1-modules=${PYASN1_MODULES_VERSION} \
    pytorch=${PYTORCH_VERSION} \
    tensorboard=${TENSORBOARD_VERSION} \
    torchvision=${PYTORCH_TORCHVISION_VERSION} && \
    echo "===> Installing dependencies using pip...." && \
    ${CONDA_DIR}/condabin/conda run -n base \
    pip install --no-cache-dir \
    pytorch-lightning==${PYTORCH_LIGHTNING_VERSION} && \
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
