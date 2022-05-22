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

CONTAINER_MLFLOW_TRACKING_CONDA_ENV_FILES =\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/environment-mlflow-tracking.yml
CONTAINER_MLFLOW_TRACKING_INCLUDE_FILES =\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/aws-config\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/bash.bashrc\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/dot-condarc
CONTAINER_MLFLOW_TRACKING_SCRIPTS =\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/entrypoint-mlflow-tracking.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/fix-permissions.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/init-copy.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/init-git-clone.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/init-set-permissions.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/parse-uri.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/s3-cp.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/s3-mb.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/s3-sync.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/secure-container.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/unpack-archive.sh

# Nginx -------------------------------------------------------------------------

CONTAINER_NGINX_CONDA_ENV_FILES =
CONTAINER_NGINX_INCLUDE_FILES =\
    $(CONTAINER_NGINX_INCLUDE_DIR)/nginx.conf
CONTAINER_NGINX_SCRIPTS =\
    $(CONTAINER_NGINX_INCLUDE_DIR)/entrypoint-nginx.sh\
    $(CONTAINER_NGINX_INCLUDE_DIR)/init-copy.sh\
    $(CONTAINER_NGINX_INCLUDE_DIR)/init-git-clone.sh\
    $(CONTAINER_NGINX_INCLUDE_DIR)/init-set-permissions.sh\
    $(CONTAINER_NGINX_INCLUDE_DIR)/parse-uri.sh\
    $(CONTAINER_NGINX_INCLUDE_DIR)/secure-container.sh

# PyTorch (CPU) -----------------------------------------------------------------

CONTAINER_PYTORCH_CPU_CONDA_ENV_FILES =\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/environment-worker.yml
CONTAINER_PYTORCH_CPU_INCLUDE_FILES =\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/aws-config\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/bash.bashrc\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/dot-condarc\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl
CONTAINER_PYTORCH_CPU_SCRIPTS =\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/entrypoint-worker.sh\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/fix-permissions.sh\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/init-copy.sh\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/init-git-clone.sh\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/init-set-permissions.sh\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/parse-uri.sh\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/run-mlflow-job.sh\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/s3-cp.sh\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/s3-mb.sh\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/s3-sync.sh\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/secure-container.sh\
    $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/unpack-archive.sh

# PyTorch (GPU) -----------------------------------------------------------------

CONTAINER_PYTORCH_GPU_CONDA_ENV_FILES =\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/environment-worker.yml
CONTAINER_PYTORCH_GPU_INCLUDE_FILES =\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/aws-config\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/bash.bashrc\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/dot-condarc\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl
CONTAINER_PYTORCH_GPU_SCRIPTS =\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/entrypoint-worker.sh\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/fix-permissions.sh\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/init-copy.sh\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/init-git-clone.sh\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/init-set-permissions.sh\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/parse-uri.sh\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/run-mlflow-job.sh\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/s3-cp.sh\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/s3-mb.sh\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/s3-sync.sh\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/secure-container.sh\
    $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/unpack-archive.sh

# restapi -----------------------------------------------------------------------

CONTAINER_RESTAPI_CONDA_ENV_FILES =\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/environment-restapi.yml
CONTAINER_RESTAPI_INCLUDE_FILES =\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/aws-config\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/bash.bashrc\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/dot-condarc\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/gunicorn.conf.py\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl\
    $(CODE_DB_MIGRATIONS_FILES)\
    wsgi.py
CONTAINER_RESTAPI_SCRIPTS =\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/entrypoint-restapi.sh\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/fix-permissions.sh\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/init-copy.sh\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/init-git-clone.sh\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/init-set-permissions.sh\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/parse-uri.sh\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/s3-cp.sh\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/s3-mb.sh\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/s3-sync.sh\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/secure-container.sh\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/unpack-archive.sh

# Tensorflow v2 (CPU) -----------------------------------------------------------

CONTAINER_TENSORFLOW2_CPU_CONDA_ENV_FILES =\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/environment-worker.yml
CONTAINER_TENSORFLOW2_CPU_INCLUDE_FILES =\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/aws-config\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/bash.bashrc\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/dot-condarc\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl
CONTAINER_TENSORFLOW2_CPU_SCRIPTS =\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/entrypoint-worker.sh\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/fix-permissions.sh\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/init-copy.sh\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/init-git-clone.sh\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/init-set-permissions.sh\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/parse-uri.sh\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/run-mlflow-job.sh\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/s3-cp.sh\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/s3-mb.sh\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/s3-sync.sh\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/secure-container.sh\
    $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/unpack-archive.sh

# Tensorflow v2 (GPU) -----------------------------------------------------------

CONTAINER_TENSORFLOW2_GPU_CONDA_ENV_FILES =\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/environment-worker.yml
CONTAINER_TENSORFLOW2_GPU_INCLUDE_FILES =\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/aws-config\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/bash.bashrc\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/dot-condarc\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl
CONTAINER_TENSORFLOW2_GPU_SCRIPTS =\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/entrypoint-worker.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/fix-permissions.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/init-copy.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/init-git-clone.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/init-set-permissions.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/parse-uri.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/run-mlflow-job.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/s3-cp.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/s3-mb.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/s3-sync.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/secure-container.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/unpack-archive.sh
