
ARG PROJECT_VERSION
ARG PROJECT_BUILD_NUMBER

FROM securing-ai/sklearn-py37:${PROJECT_VERSION}-${PROJECT_BUILD_NUMBER}

ARG TENSORFLOW2_VERSION
ARG TENSORFLOW2_BUILD=py37_0
ARG TENSORFLOW2_BASE_BUILD=0

ARG MPI4PY_VERSION=3.0.3
ARG MPI4PY_BUILD=py37_6
ARG TBB_VERSION=2020.2
ARG TBB_BUILD=intel_217

RUN echo "===> Installing Tensorflow environment...."; \
    ${CONDA_DIR}/condabin/conda install -n base -c defaults -c intel -q -y \
    mpi4py=${MPI4PY_VERSION}=${MPI4PY_BUILD} \
    tensorflow=${TENSORFLOW2_VERSION}=${TENSORFLOW2_BUILD} \
    tensorflow-base=${TENSORFLOW2_VERSION}=${TENSORFLOW2_BASE_BUILD} \
    tbb=${TBB_VERSION}=${TBB_BUILD} && \
    echo "===> Cleaning/pruning directories...." && \
    find ${CONDA_DIR} -follow -type f -name '*.a' -delete && \
    find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete && \
    ${CONDA_DIR}/condabin/conda clean -afy && \
    rm -rf /home/${AI_USER}/.cache/yarn && \
    echo "===> Fixing directory permissions...." && \
    fix-permissions.sh ${CONDA_DIR} ${AI_WORKDIR} /home/${AI_USER}

ARG MAINTAINER="James Glasbrenner <jglasbrenner@mitre.org>"
ARG PROJECT_COMPONENT

LABEL securingai.docker.project.component=${PROJECT_COMPONENT}
LABEL securingai.docker.project.component.maintainer=${MAINTAINER}
