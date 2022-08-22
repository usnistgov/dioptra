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
CODE_PKG_VERSION = 0.0.0

CONTAINER_BASE_IMAGE ?= public-base
CONTAINER_IMAGE_TAG = dev
CONTAINER_MINICONDA3_PREFIX = Miniconda3-py39_
CONTAINER_MINICONDA_VERSION = 4.11.0
CONTAINER_IBM_ART_VERSION = 1.9.*
CONTAINER_MLFLOW_VERSION = 1.*
CONTAINER_PREFECT_VERSION = 1.0.*
CONTAINER_PYTHON_VERSION = 3.9.*
CONTAINER_PYTORCH_CUDA_VERSION = cu113
CONTAINER_PYTORCH_MAJOR_MINOR_VERSION = 1.10
CONTAINER_PYTORCH_TORCHAUDIO_VERSION = 0.10.2
CONTAINER_PYTORCH_TORCHVISION_VERSION = 0.11.3
CONTAINER_PYTORCH_VERSION = $(CONTAINER_PYTORCH_MAJOR_MINOR_VERSION).2
CONTAINER_SKLEARN_VERSION = 1.0.*
CONTAINER_TENSORFLOW_VERSION = 2.9.1
CONTAINER_PYTORCH_NVIDIA_CUDA_VERSION = 11.3.1-cudnn8-runtime-ubuntu20.04
CONTAINER_TENSORFLOW_NVIDIA_CUDA_VERSION = 11.5.1-cudnn8-runtime-ubuntu20.04
