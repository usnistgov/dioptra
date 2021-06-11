#################################################################################
# CONTINUOUS INTEGRATION IMAGES                                                 #
#################################################################################

# python-build ------------------------------------------------------------------

CONTAINER_PYTHON_BUILD_CONDA_ENV_FILES =
CONTAINER_PYTHON_BUILD_INCLUDE_FILES =
CONTAINER_PYTHON_BUILD_SCRIPTS =

# Sphinx ------------------------------------------------------------------------

CONTAINER_SPHINX_CONDA_ENV_FILES =
CONTAINER_SPHINX_INCLUDE_FILES =
CONTAINER_SPHINX_SCRIPTS =

# Tox (Python 3.7) --------------------------------------------------------------

CONTAINER_TOX_PY37_CONDA_ENV_FILES =
CONTAINER_TOX_PY37_INCLUDE_FILES =
CONTAINER_TOX_PY37_SCRIPTS =

# Tox (Python 3.8) --------------------------------------------------------------

CONTAINER_TOX_PY38_CONDA_ENV_FILES =
CONTAINER_TOX_PY38_INCLUDE_FILES =
CONTAINER_TOX_PY38_SCRIPTS =

#################################################################################
# DIOPTRA TESTBED IMAGES                                                        #
#################################################################################

# MLFlow Tracking ---------------------------------------------------------------

CONTAINER_MLFLOW_TRACKING_CONDA_ENV_FILES =\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/environment-mlflow-tracking.yml
CONTAINER_MLFLOW_TRACKING_INCLUDE_FILES =\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/aws-config\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/bash.bashrc\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/dot-condarc
CONTAINER_MLFLOW_TRACKING_SCRIPTS =\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/entrypoint-mlflow-tracking.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/fix-permissions.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/parse-uri.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/s3-cp.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/s3-mb.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/s3-sync.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/secure-container.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/unpack-archive.sh

# Nginx -------------------------------------------------------------------------

CONTAINER_NGINX_CONDA_ENV_FILES =
CONTAINER_NGINX_INCLUDE_FILES =\
    $(CONTAINER_NGINX_INCLUDE_DIR)/default.conf\
    $(CONTAINER_NGINX_INCLUDE_DIR)/nginx.conf
CONTAINER_NGINX_SCRIPTS =\
    $(CONTAINER_NGINX_INCLUDE_DIR)/entrypoint-nginx.sh\
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
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/parse-uri.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/run-mlflow-job.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/s3-cp.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/s3-mb.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/s3-sync.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/secure-container.sh\
    $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/unpack-archive.sh
