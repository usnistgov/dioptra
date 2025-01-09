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
    docker/configs/build.pip.conf\
    docker/requirements/linux-$(DETECTED_ARCH)-py3.11-mlflow-tracking-requirements.txt\
    docker/shellscripts/entrypoint-mlflow-tracking.m4\
    docker/shellscripts/fix-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/wait-for-it.sh

# Nginx -------------------------------------------------------------------------

CONTAINER_NGINX_INCLUDE_FILES =\
    docker/configs/nginx.conf\
    docker/shellscripts/entrypoint-nginx.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/wait-for-it.sh

# PyTorch (CPU) -----------------------------------------------------------------

CONTAINER_PYTORCH_CPU_INCLUDE_FILES =\
    docker/configs/aws-config\
    docker/configs/build.pip.conf\
    docker/requirements/linux-$(DETECTED_ARCH)-py3.11-pytorch-cpu-requirements.txt\
    docker/shellscripts/entrypoint-worker.m4\
    docker/shellscripts/fix-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/wait-for-it.sh\
    $(CODE_PACKAGING_FILES)\
    $(CODE_SRC_FILES)

# PyTorch (GPU) -----------------------------------------------------------------

CONTAINER_PYTORCH_GPU_INCLUDE_FILES =\
    docker/configs/aws-config\
    docker/configs/build.pip.conf\
    docker/requirements/linux-amd64-py3.11-pytorch-gpu-requirements.txt\
    docker/shellscripts/entrypoint-worker.m4\
    docker/shellscripts/fix-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/wait-for-it.sh\
    $(CODE_PACKAGING_FILES)\
    $(CODE_SRC_FILES)

# restapi -----------------------------------------------------------------------

CONTAINER_RESTAPI_INCLUDE_FILES =\
    docker/configs/aws-config\
    docker/configs/build.pip.conf\
    docker/configs/gunicorn.restapi.conf.py\
    docker/requirements/linux-$(DETECTED_ARCH)-py3.11-restapi-requirements.txt\
    docker/shellscripts/entrypoint-restapi.m4\
    docker/shellscripts/fix-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/wait-for-it.sh\
    wsgi.py\
    $(CODE_PACKAGING_FILES)\
    $(CODE_SRC_FILES)

# Tensorflow v2 (CPU) -----------------------------------------------------------

CONTAINER_TENSORFLOW2_CPU_INCLUDE_FILES =\
    docker/configs/aws-config\
    docker/configs/build.pip.conf\
    docker/requirements/linux-$(DETECTED_ARCH)-py3.11-tensorflow2-cpu-requirements.txt\
    docker/shellscripts/entrypoint-worker.m4\
    docker/shellscripts/fix-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/wait-for-it.sh\
    $(CODE_PACKAGING_FILES)\
    $(CODE_SRC_FILES)

# Tensorflow v2 (GPU) -----------------------------------------------------------

CONTAINER_TENSORFLOW2_GPU_INCLUDE_FILES =\
    docker/configs/aws-config\
    docker/configs/build.pip.conf\
    docker/requirements/linux-amd64-py3.11-tensorflow2-gpu-requirements.txt\
    docker/shellscripts/entrypoint-worker.m4\
    docker/shellscripts/fix-permissions.m4\
    docker/shellscripts/parse-uri.m4\
    docker/shellscripts/wait-for-it.sh\
    $(CODE_PACKAGING_FILES)\
    $(CODE_SRC_FILES)
