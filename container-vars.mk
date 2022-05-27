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

#################################################################################
# DIOPTRA IMAGES                                                                #
#################################################################################

# MLFlow Tracking ---------------------------------------------------------------

CONTAINER_MLFLOW_TRACKING_INCLUDE_FILES =\
    docker/configs/aws-config\
    docker/configs/bash.bashrc\
    docker/configs/build.pip.conf\
    docker/configs/dot-condarc\
    docker/conda-env/environment-mlflow-tracking.yml\
    docker/shellscripts/conda-env.m4\
    docker/shellscripts/entrypoint-mlflow-tracking.m4\
    docker/shellscripts/fix-permissions.m4\
    docker/shellscripts/init-copy.m4\
    docker/shellscripts/init-git-clone.m4\
    docker/shellscripts/init-set-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/s3-cp.m4\
    docker/shellscripts/s3-mb.m4\
    docker/shellscripts/s3-sync.m4\
    docker/shellscripts/secure-container.m4\
    docker/shellscripts/unpack-archive.m4

# Nginx -------------------------------------------------------------------------

CONTAINER_NGINX_INCLUDE_FILES =\
    docker/configs/nginx.conf\
    docker/configs/nginx.default.conf\
    docker/shellscripts/entrypoint-nginx.m4\
    docker/shellscripts/init-copy.m4\
    docker/shellscripts/init-git-clone.m4\
    docker/shellscripts/init-set-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/secure-container.m4

# PyTorch (CPU) -----------------------------------------------------------------

CONTAINER_PYTORCH_CPU_INCLUDE_FILES =\
    docker/conda-env/environment-pytorch-cpu.yml\
    docker/configs/aws-config\
    docker/configs/bash.bashrc\
    docker/configs/build.pip.conf\
    docker/configs/dot-condarc\
    docker/shellscripts/conda-env.m4\
    docker/shellscripts/entrypoint-worker.m4\
    docker/shellscripts/fix-permissions.m4\
    docker/shellscripts/init-copy.m4\
    docker/shellscripts/init-git-clone.m4\
    docker/shellscripts/init-set-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/run-mlflow-job.m4\
    docker/shellscripts/s3-cp.m4\
    docker/shellscripts/s3-mb.m4\
    docker/shellscripts/s3-sync.m4\
    docker/shellscripts/secure-container.m4\
    docker/shellscripts/unpack-archive.m4\
    $(CODE_PACKAGING_FILES)\
    $(CODE_SRC_FILES)

# PyTorch (GPU) -----------------------------------------------------------------

CONTAINER_PYTORCH_GPU_INCLUDE_FILES =\
    docker/conda-env/environment-pytorch-gpu.yml\
    docker/configs/aws-config\
    docker/configs/bash.bashrc\
    docker/configs/build.pip.conf\
    docker/configs/dot-condarc\
    docker/shellscripts/conda-env.m4\
    docker/shellscripts/entrypoint-worker.m4\
    docker/shellscripts/fix-permissions.m4\
    docker/shellscripts/init-copy.m4\
    docker/shellscripts/init-git-clone.m4\
    docker/shellscripts/init-set-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/run-mlflow-job.m4\
    docker/shellscripts/s3-cp.m4\
    docker/shellscripts/s3-mb.m4\
    docker/shellscripts/s3-sync.m4\
    docker/shellscripts/secure-container.m4\
    docker/shellscripts/unpack-archive.m4\
    $(CODE_PACKAGING_FILES)\
    $(CODE_SRC_FILES)

# restapi -----------------------------------------------------------------------

CONTAINER_RESTAPI_INCLUDE_FILES =\
    docker/conda-env/environment-restapi.yml\
    docker/configs/aws-config\
    docker/configs/bash.bashrc\
    docker/configs/build.pip.conf\
    docker/configs/dot-condarc\
    docker/configs/gunicorn.restapi.conf.py\
    docker/shellscripts/conda-env.m4\
    docker/shellscripts/entrypoint-restapi.m4\
    docker/shellscripts/fix-permissions.m4\
    docker/shellscripts/init-copy.m4\
    docker/shellscripts/init-git-clone.m4\
    docker/shellscripts/init-set-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/s3-cp.m4\
    docker/shellscripts/s3-mb.m4\
    docker/shellscripts/s3-sync.m4\
    docker/shellscripts/secure-container.m4\
    docker/shellscripts/unpack-archive.m4\
    wsgi.py\
    $(CODE_DB_MIGRATIONS_FILES)\
    $(CODE_PACKAGING_FILES)\
    $(CODE_SRC_FILES)

# Tensorflow v2 (CPU) -----------------------------------------------------------

CONTAINER_TENSORFLOW2_CPU_INCLUDE_FILES =\
    docker/conda-env/environment-tensorflow2-cpu.yml\
    docker/configs/aws-config\
    docker/configs/bash.bashrc\
    docker/configs/build.pip.conf\
    docker/configs/dot-condarc\
    docker/shellscripts/conda-env.m4\
    docker/shellscripts/entrypoint-worker.m4\
    docker/shellscripts/fix-permissions.m4\
    docker/shellscripts/init-copy.m4\
    docker/shellscripts/init-git-clone.m4\
    docker/shellscripts/init-set-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/run-mlflow-job.m4\
    docker/shellscripts/s3-cp.m4\
    docker/shellscripts/s3-mb.m4\
    docker/shellscripts/s3-sync.m4\
    docker/shellscripts/secure-container.m4\
    docker/shellscripts/unpack-archive.m4\
    $(CODE_PACKAGING_FILES)\
    $(CODE_SRC_FILES)

# Tensorflow v2 (GPU) -----------------------------------------------------------

CONTAINER_TENSORFLOW2_GPU_INCLUDE_FILES =\
    docker/conda-env/environment-tensorflow2-gpu.yml\
    docker/configs/aws-config\
    docker/configs/bash.bashrc\
    docker/configs/build.pip.conf\
    docker/configs/dot-condarc\
    docker/shellscripts/conda-env.m4\
    docker/shellscripts/entrypoint-worker.m4\
    docker/shellscripts/fix-permissions.m4\
    docker/shellscripts/init-copy.m4\
    docker/shellscripts/init-git-clone.m4\
    docker/shellscripts/init-set-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/run-mlflow-job.m4\
    docker/shellscripts/s3-cp.m4\
    docker/shellscripts/s3-mb.m4\
    docker/shellscripts/s3-sync.m4\
    docker/shellscripts/secure-container.m4\
    docker/shellscripts/unpack-archive.m4\
    $(CODE_PACKAGING_FILES)\
    $(CODE_SRC_FILES)
