
ARG PROJECT_VERSION
ARG PROJECT_BUILD_NUMBER

FROM securing-ai/sklearn:${PROJECT_VERSION}-${PROJECT_BUILD_NUMBER}

ARG PYTORCH_CUDATOOLKIT_VERSION=11.0.221
ARG PYTORCH_TORCHVISION_VERSION=0.8.1

RUN echo "===> Installing PyTorch (GPU) environment...." && \
    ${CONDA_DIR}/condabin/conda install -n base -c defaults -c pytorch -q -y \
    cudatoolkit=${PYTORCH_CUDATOOLKIT_VERSION} \
    pytorch=${PYTORCH_VERSION} \
    torchvision=${PYTORCH_TORCHVISION_VERSION} && \
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
