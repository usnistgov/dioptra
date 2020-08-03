.PHONY: beautify build-all build-miniconda build-mlflow-tracking build-nginx build-postgres build-pytorch build-restapi build-sklearn build-tensorflow clean code-check code-pkg code-publish conda-create conda-update docs docs-publish help hooks pull-mitre push-mitre tests tests-integration tests-unit tox
SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

#################################################################################
# GLOBALS                                                                       #
#################################################################################

ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
else
    DETECTED_OS := $(shell sh -c "uname 2>/dev/null || echo Unknown")
endif

ifeq ($(DETECTED_OS),Darwin)
    CORES = $(shell sysctl -n hw.physicalcpu_max)
else ifeq ($(DETECTED_OS),Linux)
    CORES = $(shell lscpu -p | egrep -v '^\#' | sort -u -t, -k 2,4 | wc -l)
else
    CORES = 1
endif

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = securing-ai-lab-components
PROJECT_VERSION = 0.0.0
PROJECT_PREFIX = securing-ai
PROJECT_BUILD_DIR = build
PROJECT_DOCS_DIR = docs
PROJECT_DOCKER_DIR = docker
PROJECT_EXAMPLES_DIR = examples
PROJECT_IMAGES_LATEST :=\
    $(CONTAINER_MINICONDA_BASE_IMAGE)\
	$(CONTAINER_MLFLOW_TRACKING_IMAGE)\
	$(CONTAINER_NGINX_IMAGE)\
	$(CONTAINER_POSTGRES_IMAGE)\
	$(CONTAINER_RESTAPI_IMAGE)\
	$(CONTAINER_SKLEARN_IMAGE)\
	$(CONTAINER_PYTORCH_CPU_IMAGE)\
	$(CONTAINER_PYTORCH_GPU_IMAGE)\
	$(CONTAINER_TENSORFLOW2_CPU_IMAGE)\
	$(CONTAINER_TENSORFLOW2_GPU_IMAGE)
PROJECT_SRC_DIR = src
PROJECT_SRC_MITRE_DIR = $(PROJECT_SRC_DIR)/mitre
PROJECT_SRC_SECURINGAI_DIR = $(PROJECT_SRC_MITRE_DIR)/securingai
PROJECT_SRC_ENDPOINT_DIR = $(PROJECT_SRC_SECURINGAI_DIR)/endpoint
PROJECT_SRC_SHELLSCRIPTS_DIR = $(PROJECT_SRC_DIR)/shellscript
PROJECT_TESTS_DIR = tests

BLACK = black
COPY = cp
DOCKER = docker
DOCKER_COMPOSE = docker-compose
FIND = find
FLAKE8 = flake8
GHP_IMPORT = ghp-import
GIT = git
ISORT = isort
MKDOCS = mkdocs
MV = mv
PRE_COMMIT = pre-commit
PY ?= python3.7
PYTEST = pytest
RM = rm
SEED_ISORT_CONFIG = seed-isort-config
TOX = tox

GITLAB_CI_FILE = .gitlab-ci.yml
ISORT_CONFIG_FILE = .isort.cfg
MAKEFILE_FILE = Makefile
PRE_COMMIT_CONFIG_FILE = .pre-commit-config.yaml
SETUP_PY_FILE = setup.py
TOX_CONFIG_FILE = tox.ini

CODE_PKG_NAME = mitre-securing-ai
CODE_PKG_VERSION = $(PROJECT_VERSION)
CODE_BUILD_DIR = $(PROJECT_BUILD_DIR)/dist
CODE_INTEGRATION_TESTS_DIR = $(PROJECT_TESTS_DIR)/integration
CODE_UNIT_TESTS_DIR = $(PROJECT_TESTS_DIR)/unit
CODE_SRC_FILES := $(wildcard $(PROJECT_SRC_DIR)/mitre/**/*.py)
CODE_INTEGRATION_TESTS_FILES := $(wildcard $(CODE_INTEGRATION_TESTS_DIR)/**/*.py)
CODE_UNIT_TESTS_FILES := $(wildcard $(CODE_UNIT_TESTS_DIR)/**/*.py)
CODE_PACKAGING_FILES =\
    $(SETUP_PY_FILE)\
    $(TOX_CONFIG_FILE)\
    LICENSE\
    MANIFEST.in\
    mkdocs.yml\
    pyproject.toml
CODE_DISTRIBUTION_FILES :=\
    $(CODE_BUILD_DIR)/$(CODE_PKG_NAME)-$(CODE_PKG_VERSION).tar.gz\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl

CONTAINER_OS_VERSION = bionic
CONTAINER_OS_VERSION_NUMBER = 18.04
CONTAINER_OS_BUILD_NUMBER = 20200630
CONTAINER_BUILD_NUMBER = 1
CONTAINER_IMAGE_TAG = $(PROJECT_VERSION)-$(CONTAINER_BUILD_NUMBER)
CONTAINER_IBM_ART_VERSION = 1.3.1
CONTAINER_MINICONDA_VERSION = 4.8.3
CONTAINER_MLFLOW_VERSION = 1.9.1
CONTAINER_PYTORCH_VERSION = 1.5.1
CONTAINER_SKLEARN_VERSION = 0.22.1
CONTAINER_TENSORFLOW2_VERSION = 2.1.0

DOCS_FILES := $(wildcard $(PROJECT_DOCS_DIR)/**/*.md)
DOCS_BUILD_DIR = $(PROJECT_BUILD_DIR)/docs

PIP :=
ifeq ($(DETECTED_OS),Darwin)
    PIP += CFLAGS="-stdlib=libc++" pip
else
    PIP += pip
endif
CONDA = conda
CONDA_CHANNELS = -c defaults -c conda-forge
CONDA_ENV_BASE := python=3.7.7 pip=20.0.2 setuptools=46.1.3 setuptools-scm=3.5.0 wheel=0.34.2
ifeq ($(DETECTED_OS),Darwin)
    CONDA_ENV_BASE +=
endif
CONDA_ENV_FILE = environment.yml
CONDA_ENV_NAME = $(PROJECT_NAME)
CONDA_ENV_PIP =

GITLAB_PAGES_BRANCH = gl-pages
GITLAB_PAGES_BUILD_DIR = $(PROJECT_BUILD_DIR)/site
GITLAB_PAGES_IMPORT_OPTS =\
    -m "docs: publish ($(shell date '+%Y-%m-%dT%H:%M:%S%z'))"

ARTIFACTORY_PREFIX = artifacts.mitre.org:8200
ARTIFACTORY_IMAGES_LATEST := $(foreach image,$(PROJECT_IMAGES_LATEST),$(ARTIFACTORY_PREFIX)/$(image))

CONTAINER_MINICONDA_BASE_COMPONENT_NAME = miniconda-base
CONTAINER_MINICONDA_BASE_IMAGE = $(PROJECT_PREFIX)/$(CONTAINER_MINICONDA_BASE_COMPONENT_NAME):$(CONTAINER_IMAGE_TAG)
CONTAINER_MINICONDA_BASE_DIR = $(PROJECT_DOCKER_DIR)/$(CONTAINER_MINICONDA_BASE_COMPONENT_NAME)
CONTAINER_MINICONDA_BASE_INCLUDE_DIR = $(CONTAINER_MINICONDA_BASE_DIR)/include/etc/$(PROJECT_PREFIX)/docker
CONTAINER_MINICONDA_BASE_DOCKERFILE = $(CONTAINER_MINICONDA_BASE_DIR)/Dockerfile
CONTAINER_MINICONDA_BASE_INCLUDE_FILES =\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/aws-config\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/bash.bashrc\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/dot-condarc
CONTAINER_MINICONDA_BASE_SCRIPTS =\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/fix-permissions.sh\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/install-python-modules.sh\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/s3-cp.sh\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/unpack-archive.sh
CONTAINER_MINICONDA_BASE_SHELLSCRIPTS_EXT = $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/%.sh : $(PROJECT_SRC_SHELLSCRIPTS_DIR)/%.m4

CONTAINER_MLFLOW_TRACKING_COMPONENT_NAME = mlflow-tracking
CONTAINER_MLFLOW_TRACKING_IMAGE = $(PROJECT_PREFIX)/$(CONTAINER_MLFLOW_TRACKING_COMPONENT_NAME):$(CONTAINER_IMAGE_TAG)
CONTAINER_MLFLOW_TRACKING_DIR = $(PROJECT_DOCKER_DIR)/$(CONTAINER_MLFLOW_TRACKING_COMPONENT_NAME)
CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR = $(CONTAINER_MLFLOW_TRACKING_DIR)/include/etc/$(PROJECT_PREFIX)/docker
CONTAINER_MLFLOW_TRACKING_DOCKERFILE = $(CONTAINER_MLFLOW_TRACKING_DIR)/Dockerfile
CONTAINER_MLFLOW_TRACKING_INCLUDE_FILES =
CONTAINER_MLFLOW_TRACKING_SCRIPTS =\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/entrypoint-mlflow-tracking.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/s3-mb.sh
CONTAINER_MLFLOW_TRACKING_SHELLSCRIPTS_EXT = $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/%.sh : $(PROJECT_SRC_SHELLSCRIPTS_DIR)/%.m4

CONTAINER_NGINX_COMPONENT_NAME = nginx
CONTAINER_NGINX_IMAGE = $(PROJECT_PREFIX)/$(CONTAINER_NGINX_COMPONENT_NAME):$(CONTAINER_IMAGE_TAG)
CONTAINER_NGINX_DIR = $(PROJECT_DOCKER_DIR)/$(CONTAINER_NGINX_COMPONENT_NAME)
CONTAINER_NGINX_INCLUDE_DIR = $(CONTAINER_NGINX_DIR)/include/etc/$(PROJECT_PREFIX)/docker
CONTAINER_NGINX_DOCKERFILE = $(CONTAINER_NGINX_DIR)/Dockerfile
CONTAINER_NGINX_INCLUDE_FILES =\
    $(CONTAINER_NGINX_INCLUDE_DIR)/nginx.conf
CONTAINER_NGINX_SCRIPTS =\
    $(CONTAINER_NGINX_INCLUDE_DIR)/entrypoint-nginx.sh\
    $(CONTAINER_NGINX_INCLUDE_DIR)/fix-permissions.sh\
    $(CONTAINER_NGINX_INCLUDE_DIR)/secure-container.sh
CONTAINER_NGINX_SHELLSCRIPTS_EXT = $(CONTAINER_NGINX_INCLUDE_DIR)/%.sh : $(PROJECT_SRC_SHELLSCRIPTS_DIR)/%.m4

CONTAINER_POSTGRES_COMPONENT_NAME = postgres
CONTAINER_POSTGRES_IMAGE = $(PROJECT_PREFIX)/$(CONTAINER_POSTGRES_COMPONENT_NAME):$(CONTAINER_IMAGE_TAG)
CONTAINER_POSTGRES_DIR = $(PROJECT_DOCKER_DIR)/$(CONTAINER_POSTGRES_COMPONENT_NAME)
CONTAINER_POSTGRES_INCLUDE_DIR = $(CONTAINER_POSTGRES_DIR)/include/etc/$(PROJECT_PREFIX)/docker
CONTAINER_POSTGRES_DOCKERFILE = $(CONTAINER_POSTGRES_DIR)/Dockerfile
CONTAINER_POSTGRES_INCLUDE_FILES =
CONTAINER_POSTGRES_SCRIPTS =
CONTAINER_POSTGRES_SHELLSCRIPTS_EXT = $(CONTAINER_POSTGRES_INCLUDE_DIR)/%.sh : $(PROJECT_SRC_SHELLSCRIPTS_DIR)/%.m4

CONTAINER_RESTAPI_COMPONENT_NAME = restapi
CONTAINER_RESTAPI_IMAGE = $(PROJECT_PREFIX)/$(CONTAINER_RESTAPI_COMPONENT_NAME):$(CONTAINER_IMAGE_TAG)
CONTAINER_RESTAPI_DIR = $(PROJECT_DOCKER_DIR)/$(CONTAINER_RESTAPI_COMPONENT_NAME)
CONTAINER_RESTAPI_INCLUDE_DIR = $(CONTAINER_RESTAPI_DIR)/include/etc/$(PROJECT_PREFIX)/docker
CONTAINER_RESTAPI_DOCKERFILE = $(CONTAINER_RESTAPI_DIR)/Dockerfile
CONTAINER_RESTAPI_INCLUDE_FILES =\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/uwsgi.ini\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/wsgi.py
CONTAINER_RESTAPI_SCRIPTS =\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/entrypoint-restapi.sh\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/secure-container.sh
CONTAINER_RESTAPI_SHELLSCRIPTS_EXT = $(CONTAINER_RESTAPI_INCLUDE_DIR)/%.sh : $(PROJECT_SRC_SHELLSCRIPTS_DIR)/%.m4

CONTAINER_SKLEARN_COMPONENT_NAME = sklearn-py37
CONTAINER_SKLEARN_IMAGE = $(PROJECT_PREFIX)/$(CONTAINER_SKLEARN_COMPONENT_NAME):$(CONTAINER_IMAGE_TAG)
CONTAINER_SKLEARN_DIR = $(PROJECT_DOCKER_DIR)/$(CONTAINER_SKLEARN_COMPONENT_NAME)
CONTAINER_SKLEARN_INCLUDE_DIR = $(CONTAINER_SKLEARN_DIR)/include/etc/$(PROJECT_PREFIX)/docker
CONTAINER_SKLEARN_DOCKERFILE = $(CONTAINER_SKLEARN_DIR)/Dockerfile
CONTAINER_SKLEARN_INCLUDE_FILES =
CONTAINER_SKLEARN_SCRIPTS =\
    $(CONTAINER_SKLEARN_INCLUDE_DIR)/entrypoint-sklearn.sh\
    $(CONTAINER_SKLEARN_INCLUDE_DIR)/restrict-network-access.sh\
    $(CONTAINER_SKLEARN_INCLUDE_DIR)/secure-container.sh
CONTAINER_SKLEARN_SHELLSCRIPTS_EXT = $(CONTAINER_SKLEARN_INCLUDE_DIR)/%.sh : $(PROJECT_SRC_SHELLSCRIPTS_DIR)/%.m4

CONTAINER_PYTORCH_CPU_COMPONENT_NAME = pytorch-cpu-py37
CONTAINER_PYTORCH_CPU_IMAGE = $(PROJECT_PREFIX)/$(CONTAINER_PYTORCH_CPU_COMPONENT_NAME):$(CONTAINER_IMAGE_TAG)
CONTAINER_PYTORCH_CPU_DIR = $(PROJECT_DOCKER_DIR)/$(CONTAINER_PYTORCH_CPU_COMPONENT_NAME)
CONTAINER_PYTORCH_CPU_INCLUDE_DIR = $(CONTAINER_PYTORCH_CPU_DIR)/include/etc/$(PROJECT_PREFIX)/docker
CONTAINER_PYTORCH_CPU_DOCKERFILE = $(CONTAINER_PYTORCH_CPU_DIR)/Dockerfile
CONTAINER_PYTORCH_CPU_INCLUDE_FILES =
CONTAINER_PYTORCH_CPU_SCRIPTS =
CONTAINER_PYTORCH_CPU_SHELLSCRIPTS_EXT = $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)/%.sh : $(PROJECT_SRC_SHELLSCRIPTS_DIR)/%.m4

CONTAINER_PYTORCH_GPU_COMPONENT_NAME = pytorch-gpu-py37
CONTAINER_PYTORCH_GPU_IMAGE = $(PROJECT_PREFIX)/$(CONTAINER_PYTORCH_GPU_COMPONENT_NAME):$(CONTAINER_IMAGE_TAG)
CONTAINER_PYTORCH_GPU_DIR = $(PROJECT_DOCKER_DIR)/$(CONTAINER_PYTORCH_GPU_COMPONENT_NAME)
CONTAINER_PYTORCH_GPU_INCLUDE_DIR = $(CONTAINER_PYTORCH_GPU_DIR)/include/etc/$(PROJECT_PREFIX)/docker
CONTAINER_PYTORCH_GPU_DOCKERFILE = $(CONTAINER_PYTORCH_GPU_DIR)/Dockerfile
CONTAINER_PYTORCH_GPU_INCLUDE_FILES =
CONTAINER_PYTORCH_GPU_SCRIPTS =
CONTAINER_PYTORCH_GPU_SHELLSCRIPTS_EXT = $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)/%.sh : $(PROJECT_SRC_SHELLSCRIPTS_DIR)/%.m4

CONTAINER_TENSORFLOW2_CPU_COMPONENT_NAME = tensorflow2-cpu-py37
CONTAINER_TENSORFLOW2_CPU_IMAGE = $(PROJECT_PREFIX)/$(CONTAINER_TENSORFLOW2_CPU_COMPONENT_NAME):$(CONTAINER_IMAGE_TAG)
CONTAINER_TENSORFLOW2_CPU_DIR = $(PROJECT_DOCKER_DIR)/$(CONTAINER_TENSORFLOW2_CPU_COMPONENT_NAME)
CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR = $(CONTAINER_TENSORFLOW2_CPU_DIR)/include/etc/$(PROJECT_PREFIX)/docker
CONTAINER_TENSORFLOW2_CPU_DOCKERFILE = $(CONTAINER_TENSORFLOW2_CPU_DIR)/Dockerfile
CONTAINER_TENSORFLOW2_CPU_INCLUDE_FILES =
CONTAINER_TENSORFLOW2_CPU_SCRIPTS =
CONTAINER_TENSORFLOW2_CPU_SHELLSCRIPTS_EXT = $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)/%.sh : $(PROJECT_SRC_SHELLSCRIPTS_DIR)/%.m4

CONTAINER_TENSORFLOW2_GPU_COMPONENT_NAME = tensorflow2-gpu-py37
CONTAINER_TENSORFLOW2_GPU_IMAGE = $(PROJECT_PREFIX)/$(CONTAINER_TENSORFLOW2_GPU_COMPONENT_NAME):$(CONTAINER_IMAGE_TAG)
CONTAINER_TENSORFLOW2_GPU_DIR = $(PROJECT_DOCKER_DIR)/$(CONTAINER_TENSORFLOW2_GPU_COMPONENT_NAME)
CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR = $(CONTAINER_TENSORFLOW2_GPU_DIR)/include/etc/$(PROJECT_PREFIX)/docker
CONTAINER_TENSORFLOW2_GPU_DOCKERFILE = $(CONTAINER_TENSORFLOW2_GPU_DIR)/Dockerfile
CONTAINER_TENSORFLOW2_GPU_INCLUDE_FILES =
CONTAINER_TENSORFLOW2_GPU_SCRIPTS =
CONTAINER_TENSORFLOW2_GPU_SHELLSCRIPTS_EXT = $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)/%.sh : $(PROJECT_SRC_SHELLSCRIPTS_DIR)/%.m4

EXAMPLES_TENSORFLOW_MNIST_DIR = $(PROJECT_EXAMPLES_DIR)/tensorflow-mnist-classifier
EXAMPLES_TENSORFLOW_MNIST_SCRIPTS =\
    $(EXAMPLES_TENSORFLOW_MNIST_DIR)/docker-gpu.sh
EXAMPLES_TENSORFLOW_MNIST_SHELLSCRIPTS_EXT = $(EXAMPLES_TENSORFLOW_MNIST_DIR)/%.sh : $(EXAMPLES_TENSORFLOW_MNIST_DIR)/%.m4

BEAUTIFY_SENTINEL = $(PROJECT_BUILD_DIR)/.beautify.sentinel
CODE_INTEGRATION_TESTS_SENTINEL = $(PROJECT_BUILD_DIR)/.integration-tests.sentinel
CODE_UNIT_TESTS_SENTINEL = $(PROJECT_BUILD_DIR)/.unit-tests.sentinel
CONDA_CREATE_SENTINEL = $(PROJECT_BUILD_DIR)/.conda-create.sentinel
CONDA_UPDATE_SENTINEL = $(PROJECT_BUILD_DIR)/.conda-update.sentinel
CONDA_ENV_PIP_INSTALL_SENTINEL = $(PROJECT_BUILD_DIR)/.conda-env-pip-install.sentinel
CONTAINER_MINICONDA_BASE_BUILD_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_MINICONDA_BASE_COMPONENT_NAME)-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_MINICONDA_BASE_PULL_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_MINICONDA_BASE_COMPONENT_NAME)-pulled-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_MINICONDA_BASE_PUSH_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_MINICONDA_BASE_COMPONENT_NAME)-pushed-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_MLFLOW_TRACKING_BUILD_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_MLFLOW_TRACKING_COMPONENT_NAME)-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_MLFLOW_TRACKING_PULL_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_MLFLOW_TRACKING_COMPONENT_NAME)-pulled-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_MLFLOW_TRACKING_PUSH_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_MLFLOW_TRACKING_COMPONENT_NAME)-pushed-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_NGINX_BUILD_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_NGINX_COMPONENT_NAME)-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_NGINX_PULL_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_NGINX_COMPONENT_NAME)-pulled-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_NGINX_PUSH_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_NGINX_COMPONENT_NAME)-pushed-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_POSTGRES_BUILD_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_POSTGRES_COMPONENT_NAME)-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_POSTGRES_PULL_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_POSTGRES_COMPONENT_NAME)-pulled-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_POSTGRES_PUSH_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_POSTGRES_COMPONENT_NAME)-pushed-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_RESTAPI_BUILD_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_RESTAPI_COMPONENT_NAME)-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_RESTAPI_PULL_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_RESTAPI_COMPONENT_NAME)-pulled-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_RESTAPI_PUSH_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_RESTAPI_COMPONENT_NAME)-pushed-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_SKLEARN_BUILD_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_SKLEARN_COMPONENT_NAME)-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_SKLEARN_PULL_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_SKLEARN_COMPONENT_NAME)-pulled-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_SKLEARN_PUSH_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_SKLEARN_COMPONENT_NAME)-pushed-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_PYTORCH_CPU_BUILD_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_PYTORCH_CPU_COMPONENT_NAME)-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_PYTORCH_CPU_PULL_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_PYTORCH_CPU_COMPONENT_NAME)-pulled-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_PYTORCH_CPU_PUSH_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_PYTORCH_CPU_COMPONENT_NAME)-pushed-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_PYTORCH_GPU_BUILD_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_PYTORCH_GPU_COMPONENT_NAME)-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_PYTORCH_GPU_PULL_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_PYTORCH_GPU_COMPONENT_NAME)-pulled-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_PYTORCH_GPU_PUSH_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_PYTORCH_GPU_COMPONENT_NAME)-pushed-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_TENSORFLOW2_CPU_BUILD_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_TENSORFLOW2_CPU_COMPONENT_NAME)-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_TENSORFLOW2_CPU_PULL_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_TENSORFLOW2_CPU_COMPONENT_NAME)-pulled-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_TENSORFLOW2_CPU_PUSH_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_TENSORFLOW2_CPU_COMPONENT_NAME)-pushed-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_TENSORFLOW2_GPU_BUILD_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_TENSORFLOW2_GPU_COMPONENT_NAME)-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_TENSORFLOW2_GPU_PULL_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_TENSORFLOW2_GPU_COMPONENT_NAME)-pulled-tag-$(CONTAINER_IMAGE_TAG).sentinel
CONTAINER_TENSORFLOW2_GPU_PUSH_SENTINEL = $(PROJECT_BUILD_DIR)/.docker-image-$(CONTAINER_TENSORFLOW2_GPU_COMPONENT_NAME)-pushed-tag-$(CONTAINER_IMAGE_TAG).sentinel
DOCS_SENTINEL = $(PROJECT_BUILD_DIR)/.docs.sentinel
GITLAB_PAGES_SENTINEL = $(PROJECT_BUILD_DIR)/.gitlab-pages-push.sentinel
LINTING_SENTINEL = $(PROJECT_BUILD_DIR)/.linting.sentinel
PRE_COMMIT_HOOKS_SENTINEL = $(PROJECT_BUILD_DIR)/.pre-commit-hooks.sentinel
TOX_SENTINEL = $(PROJECT_BUILD_DIR)/.tox.sentinel
TYPE_CHECK_SENTINEL = $(PROJECT_BUILD_DIR)/.type-check.sentinel

#################################################################################
# FUNCTIONS                                                                     #
#################################################################################

define cleanup
    $(FIND) $(1) -name "__pycache__" -type d -exec $(RM) -rf {} +
    $(FIND) $(1) -name "*.py[co]" -type f -exec $(RM) -rf {} +
endef

define create_conda_env
    bash -lc "\
    $(CONDA) create -n $(CONDA_ENV_NAME) $(CONDA_CHANNELS) -y $(CONDA_ENV_BASE)\
    "
endef

define make_subdirectory
    mkdir -p "$(strip $(1))"
endef

define package_code
    $(PY) $(SETUP_PY_FILE) sdist -d $(1)
    $(PY) $(SETUP_PY_FILE) bdist_wheel -d $(1)
endef

define pull_docker_images
    @$(foreach image,$(1),\
        echo "Pulling image $(image)";\
        echo "==========================================";\
        $(DOCKER) pull $(ARTIFACTORY_PREFIX)/$(image) || exit 1;\
        $(DOCKER) tag $(ARTIFACTORY_PREFIX)/$(image) $(image) || exit 1;\
        $(DOCKER) rmi $(ARTIFACTORY_PREFIX)/$(image) || exit 1;\
        echo "";)
endef

define push_docker_images
    @$(foreach image,$(1),\
        echo "Pushing image $(image)";\
		echo "==========================================";\
        $(DOCKER) tag $(image) $(ARTIFACTORY_PREFIX)/$(image) || exit 1;\
        $(DOCKER) push $(ARTIFACTORY_PREFIX)/$(image) || exit 1;\
        $(DOCKER) rmi $(ARTIFACTORY_PREFIX)/$(image) || exit 1;\
        echo "";)
endef

define push_gitlab_pages
    $(COPY) $(GITLAB_CI_FILE) $(3)
    $(GHP_IMPORT) $(1) -b $(2) $(3)
    $(GIT) push origin $(2)
endef

define pre_commit_cmd
    $(PRE_COMMIT) $(1)
endef

define run_argbash
    $(call run_docker,\
        run\
        -it\
        --rm\
        -e PROGRAM=argbash\
        -v $(strip $(1)):/work\
        -v $(strip $(2)):/output\
        matejak/argbash:latest\
        $(strip $(3)))
endef

define run_build_script
    CORES=$(CORES)\
    IMAGE_TAG=$(strip $(2))\
    OS_VERSION=$(CONTAINER_OS_VERSION) \
    OS_VERSION_NUMBER=$(CONTAINER_OS_VERSION_NUMBER) \
    OS_BUILD_NUMBER=$(CONTAINER_OS_BUILD_NUMBER) \
    PROJECT_PREFIX=$(PROJECT_PREFIX)\
    PROJECT_VERSION=$(PROJECT_VERSION)\
    PROJECT_COMPONENT=$(strip $(1))\
    PROJECT_BUILD_NUMBER=$(strip $(3))\
    IBM_ART_VERSION=$(CONTAINER_IBM_ART_VERSION)\
    MINICONDA_VERSION=$(CONTAINER_MINICONDA_VERSION)\
    MLFLOW_VERSION=$(CONTAINER_MLFLOW_VERSION)\
    PYTORCH_VERSION=$(CONTAINER_PYTORCH_VERSION)\
    SKLEARN_VERSION=$(CONTAINER_SKLEARN_VERSION)\
    TENSORFLOW2_VERSION=$(CONTAINER_TENSORFLOW2_VERSION)\
    docker/build.sh
endef

define run_docker
    $(DOCKER) $(1)
endef

define run_docker_compose
    $(DOCKER_COMPOSE) $(1)
endef

define run_flake8
    $(FLAKE8) $(1)
endef

define run_isort
    $(FIND) $(1) -name "*.py" -type f -exec $(ISORT) {} +
endef

define run_mkdocs
    $(MKDOCS) $(1)
endef

define run_mypy
    $(MYPY) $(1)
endef

define run_pip_install
    bash -lc "\
	$(CONDA) activate $(CONDA_ENV_NAME);\
    $(PIP) install $(1);\
	$(CONDA) deactivate\
	"
endef

define run_pytest
    $(PYTEST) $(1)
endef

define run_python_black
    $(BLACK) $(1)
endef

define run_seed_isort_config
    $(SEED_ISORT_CONFIG) $(1)
endef

define run_tox
    $(TOX) $(1)
endef

define save_image_id_file
    @echo "$(PROJECT_PREFIX)/$(1):$(2)" > $(3)
endef

define save_sentinel_file
	@touch $(1)
endef

define split_string_and_get_word
    $(word $3,$(subst $2, ,$1))
endef

define update_conda_env
    bash -lc "\
    $(CONDA) env update --file $(CONDA_ENV_FILE)\
    "
endef

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Reformat code
beautify: $(BEAUTIFY_SENTINEL)

## Build all Docker images in project
build-all: build-miniconda build-mlflow-tracking build-nginx build-postgres build-restapi build-sklearn build-pytorch build-tensorflow

## Build the base Miniconda Docker image
build-miniconda: $(CONTAINER_MINICONDA_BASE_BUILD_SENTINEL)

## Build the MLFlow Tracking Docker image
build-mlflow-tracking: build-miniconda $(CONTAINER_MLFLOW_TRACKING_BUILD_SENTINEL)

## Build the nginx Docker image
build-nginx: $(CONTAINER_NGINX_BUILD_SENTINEL)

## Build the postgres Docker image
build-postgres: $(CONTAINER_POSTGRES_BUILD_SENTINEL)

## Build the PyTorch Docker images
build-pytorch: build-sklearn $(CONTAINER_PYTORCH_CPU_BUILD_SENTINEL) $(CONTAINER_PYTORCH_GPU_BUILD_SENTINEL)

## Build the restapi Docker image
build-restapi: code-pkg build-miniconda $(CONTAINER_RESTAPI_BUILD_SENTINEL)

## Build the scikit-learn Docker image
build-sklearn: build-miniconda $(CONTAINER_SKLEARN_BUILD_SENTINEL)

## Build the Tensorflow Docker image
build-tensorflow: build-sklearn $(CONTAINER_TENSORFLOW2_CPU_BUILD_SENTINEL) $(CONTAINER_TENSORFLOW2_GPU_BUILD_SENTINEL)

## Remove temporary files
clean:
	$(call cleanup,$(PROJECT_SRC_DIR))
	$(call cleanup,$(PROJECT_TESTS_DIR))

## Lint and type check the source code
code-check: $(LINTING_SENTINEL) $(TYPE_CHECK_SENTINEL)

## Package source code for distribution
code-pkg: $(CODE_DISTRIBUTION_FILES)

## Publish source code to the MITRE artifactory
code-publish: code-pkg

## Create conda-based virtual environment
conda-create: $(CONDA_CREATE_SENTINEL)

## Update conda-based virtual environment
conda-update: conda-create $(CONDA_UPDATE_SENTINEL) $(CONDA_ENV_PIP_INSTALL_SENTINEL)

## Build project documentation
docs: $(DOCS_SENTINEL)

## Publish documentation to gl-pages branch
docs-publish: $(GITLAB_PAGES_SENTINEL)

## Generate support files needed for running the examples
examples: $(EXAMPLES_TENSORFLOW_MNIST_SCRIPTS)

## Install pre-commit hooks
hooks: $(PRE_COMMIT_HOOKS_SENTINEL)

## Pull latest docker images from the MITRE artifactory and retag
pull-mitre: $(CONTAINER_PULL_SENTINEL)

## Push docker images to the MITRE artifactory
push-mitre: $(CONTAINER_PUSH_SENTINEL)

## Run all tests
tests: tests-unit tests-integration

## Run integration tests
tests-integration: $(CODE_INTEGRATION_TESTS_SENTINEL)

## Run unit tests
tests-unit: $(CODE_UNIT_TESTS_SENTINEL)

## Run all tests using tox
tox: $(TOX_SENTINEL)

#################################################################################
# PROJECT SUPPORT RULES                                                         #
#################################################################################

$(BEAUTIFY_SENTINEL): $(CODE_SRC_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) $(ISORT_CONFIG_FILE)
	$(call make_subdirectory,$(@D))
	$(call run_python_black,$(PROJECT_SRC_ENDPOINT_DIR) $(PROJECT_TESTS_DIR))
	$(call run_isort,$(PROJECT_SRC_ENDPOINT_DIR))
	$(call run_isort,$(PROJECT_TESTS_DIR))
	$(call save_sentinel_file,$@)

$(CODE_INTEGRATION_TESTS_SENTINEL): $(CODE_INTEGRATION_TESTS_FILES)
	$(call make_subdirectory,$(@D))
	$(call run_pytest,$(CODE_INTEGRATION_TESTS_DIR))
	$(call save_sentinel_file,$@)

$(CODE_UNIT_TESTS_SENTINEL): $(CODE_UNIT_TESTS_FILES)
	$(call make_subdirectory,$(@D))
	$(call run_pytest,--cov=mitre --cov-report=html $(CODE_UNIT_TESTS_DIR))
	$(call save_sentinel_file,$@)

$(CODE_DISTRIBUTION_FILES): $(CODE_PACKAGING_FILES) $(CODE_SRC_FILES) $(DOCS_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES)
	$(call make_subdirectory,$(@D))
	$(call package_code,$(CODE_BUILD_DIR))
	@echo ""
	@echo "$(CODE_PKG_NAME) packaged for distribution in $(CODE_BUILD_DIR)"

$(CONDA_CREATE_SENTINEL):
	$(call make_subdirectory,$(@D))
	$(call create_conda_env)
	$(call save_sentinel_file,$@)

$(CONDA_UPDATE_SENTINEL): $(CONDA_ENV_FILE)
	$(call make_subdirectory,$(@D))
	$(call update_conda_env)
	$(call save_sentinel_file,$@)

$(CONDA_ENV_PIP_INSTALL_SENTINEL): $(MAKEFILE_FILE)
	$(call make_subdirectory,$(@D))
ifdef $(CONDA_ENV_PIP)
	$(call run_pip_install,$(subst ",,$(CONDA_ENV_PIP)))
endif
	$(call save_sentinel_file,$@)

$(CONTAINER_MINICONDA_BASE_BUILD_SENTINEL): $(CONTAINER_MINICONDA_BASE_DOCKERFILE) $(CONTAINER_MINICONDA_BASE_INCLUDE_FILES) $(CONTAINER_MINICONDA_BASE_SCRIPTS)
	$(call make_subdirectory,$(@D))
	$(call run_build_script,$(CONTAINER_MINICONDA_BASE_COMPONENT_NAME),$(CONTAINER_IMAGE_TAG),$(CONTAINER_BUILD_NUMBER))
	$(call save_sentinel_file,$(CONTAINER_MINICONDA_BASE_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_MINICONDA_BASE_PULL_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call pull_docker_images,$(CONTAINER_MINICONDA_BASE_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_MINICONDA_BASE_BUILD_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_MINICONDA_BASE_PUSH_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call push_docker_images,$(CONTAINER_MINICONDA_BASE_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_MINICONDA_BASE_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_MINICONDA_BASE_SCRIPTS): $(CONTAINER_MINICONDA_BASE_SHELLSCRIPTS_EXT) | $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)
	$(call run_argbash,\
		$(PROJECT_DIR)/$(PROJECT_SRC_SHELLSCRIPTS_DIR),\
		$(PROJECT_DIR)/$(CONTAINER_MINICONDA_BASE_INCLUDE_DIR),\
		-o /output/$(shell basename '$@') /work/$(shell basename '$<'))

$(CONTAINER_MLFLOW_TRACKING_BUILD_SENTINEL): $(CONTAINER_MLFLOW_TRACKING_DOCKERFILE) $(CONTAINER_MLFLOW_TRACKING_INCLUDE_FILES) $(CONTAINER_MLFLOW_TRACKING_SCRIPTS)
	$(call make_subdirectory,$(@D))
	$(call run_build_script,$(CONTAINER_MLFLOW_TRACKING_COMPONENT_NAME),$(CONTAINER_IMAGE_TAG),$(CONTAINER_BUILD_NUMBER))
	$(call save_sentinel_file,$(CONTAINER_MLFLOW_TRACKING_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_MLFLOW_TRACKING_PULL_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call pull_docker_images,$(CONTAINER_MLFLOW_TRACKING_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_MLFLOW_TRACKING_BUILD_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_MLFLOW_TRACKING_PUSH_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call push_docker_images,$(CONTAINER_MLFLOW_TRACKING_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_MLFLOW_TRACKING_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_MLFLOW_TRACKING_SCRIPTS): $(CONTAINER_MLFLOW_TRACKING_SHELLSCRIPTS_EXT) | $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)
	$(call run_argbash,\
		$(PROJECT_DIR)/$(PROJECT_SRC_SHELLSCRIPTS_DIR),\
		$(PROJECT_DIR)/$(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR),\
		-o /output/$(shell basename '$@') /work/$(shell basename '$<'))

$(CONTAINER_NGINX_BUILD_SENTINEL): $(CONTAINER_NGINX_DOCKERFILE) $(CONTAINER_NGINX_INCLUDE_FILES) $(CONTAINER_NGINX_SCRIPTS)
	$(call make_subdirectory,$(@D))
	$(call run_build_script,$(CONTAINER_NGINX_COMPONENT_NAME),$(CONTAINER_IMAGE_TAG),$(CONTAINER_BUILD_NUMBER))
	$(call save_sentinel_file,$(CONTAINER_NGINX_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_NGINX_PULL_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call pull_docker_images,$(CONTAINER_NGINX_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_NGINX_BUILD_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_NGINX_PUSH_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call push_docker_images,$(CONTAINER_NGINX_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_NGINX_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_NGINX_SCRIPTS): $(CONTAINER_NGINX_SHELLSCRIPTS_EXT) | $(CONTAINER_NGINX_INCLUDE_DIR)
	$(call run_argbash,\
		$(PROJECT_DIR)/$(PROJECT_SRC_SHELLSCRIPTS_DIR),\
		$(PROJECT_DIR)/$(CONTAINER_NGINX_INCLUDE_DIR),\
		-o /output/$(shell basename '$@') /work/$(shell basename '$<'))

$(CONTAINER_POSTGRES_BUILD_SENTINEL): $(CONTAINER_POSTGRES_DOCKERFILE) $(CONTAINER_POSTGRES_INCLUDE_FILES) $(CONTAINER_POSTGRES_SCRIPTS)
	$(call make_subdirectory,$(@D))
	$(call run_build_script,$(CONTAINER_POSTGRES_COMPONENT_NAME),$(CONTAINER_IMAGE_TAG),$(CONTAINER_BUILD_NUMBER))
	$(call save_sentinel_file,$(CONTAINER_POSTGRES_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_POSTGRES_PULL_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call pull_docker_images,$(CONTAINER_POSTGRES_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_POSTGRES_BUILD_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_POSTGRES_PUSH_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call push_docker_images,$(CONTAINER_POSTGRES_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_POSTGRES_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_POSTGRES_SCRIPTS): $(CONTAINER_POSTGRES_SHELLSCRIPTS_EXT) | $(CONTAINER_POSTGRES_INCLUDE_DIR)
	$(call run_argbash,\
		$(PROJECT_DIR)/$(PROJECT_SRC_SHELLSCRIPTS_DIR),\
		$(PROJECT_DIR)/$(CONTAINER_POSTGRES_INCLUDE_DIR),\
		-o /output/$(shell basename '$@') /work/$(shell basename '$<'))

$(CONTAINER_RESTAPI_BUILD_SENTINEL): $(CONTAINER_RESTAPI_DOCKERFILE) $(CONTAINER_RESTAPI_INCLUDE_FILES) $(CONTAINER_RESTAPI_SCRIPTS)
	$(call make_subdirectory,$(@D))
	$(call run_build_script,$(CONTAINER_RESTAPI_COMPONENT_NAME),$(CONTAINER_IMAGE_TAG),$(CONTAINER_BUILD_NUMBER))
	$(call save_sentinel_file,$(CONTAINER_RESTAPI_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_RESTAPI_PULL_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call pull_docker_images,$(CONTAINER_RESTAPI_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_RESTAPI_BUILD_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_RESTAPI_PUSH_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call push_docker_images,$(CONTAINER_RESTAPI_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_RESTAPI_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_RESTAPI_SCRIPTS): $(CONTAINER_RESTAPI_SHELLSCRIPTS_EXT) | $(CONTAINER_RESTAPI_INCLUDE_DIR)
	$(call run_argbash,\
		$(PROJECT_DIR)/$(PROJECT_SRC_SHELLSCRIPTS_DIR),\
		$(PROJECT_DIR)/$(CONTAINER_RESTAPI_INCLUDE_DIR),\
		-o /output/$(shell basename '$@') /work/$(shell basename '$<'))

$(CONTAINER_SKLEARN_BUILD_SENTINEL): $(CONTAINER_SKLEARN_DOCKERFILE) $(CONTAINER_SKLEARN_INCLUDE_FILES) $(CONTAINER_SKLEARN_SCRIPTS)
	$(call make_subdirectory,$(@D))
	$(call run_build_script,$(CONTAINER_SKLEARN_COMPONENT_NAME),$(CONTAINER_IMAGE_TAG),$(CONTAINER_BUILD_NUMBER))
	$(call save_sentinel_file,$(CONTAINER_SKLEARN_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_SKLEARN_PULL_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call pull_docker_images,$(CONTAINER_SKLEARN_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_SKLEARN_BUILD_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_SKLEARN_PUSH_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call push_docker_images,$(CONTAINER_SKLEARN_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_SKLEARN_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_SKLEARN_SCRIPTS): $(CONTAINER_SKLEARN_SHELLSCRIPTS_EXT) | $(CONTAINER_SKLEARN_INCLUDE_DIR)
	$(call run_argbash,\
		$(PROJECT_DIR)/$(PROJECT_SRC_SHELLSCRIPTS_DIR),\
		$(PROJECT_DIR)/$(CONTAINER_SKLEARN_INCLUDE_DIR),\
		-o /output/$(shell basename '$@') /work/$(shell basename '$<'))

$(CONTAINER_PYTORCH_CPU_BUILD_SENTINEL): $(CONTAINER_PYTORCH_CPU_DOCKERFILE) $(CONTAINER_PYTORCH_CPU_INCLUDE_FILES) $(CONTAINER_PYTORCH_CPU_SCRIPTS)
	$(call make_subdirectory,$(@D))
	$(call run_build_script,$(CONTAINER_PYTORCH_CPU_COMPONENT_NAME),$(CONTAINER_IMAGE_TAG),$(CONTAINER_BUILD_NUMBER))
	$(call save_sentinel_file,$(CONTAINER_PYTORCH_CPU_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_PYTORCH_CPU_PULL_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call pull_docker_images,$(CONTAINER_PYTORCH_CPU_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_PYTORCH_CPU_BUILD_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_PYTORCH_CPU_PUSH_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call push_docker_images,$(CONTAINER_PYTORCH_CPU_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_PYTORCH_CPU_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_PYTORCH_CPU_SCRIPTS): $(CONTAINER_PYTORCH_CPU_SHELLSCRIPTS_EXT) | $(CONTAINER_PYTORCH_CPU_INCLUDE_DIR)
	$(call run_argbash,\
		$(PROJECT_DIR)/$(PROJECT_SRC_SHELLSCRIPTS_DIR),\
		$(PROJECT_DIR)/$(CONTAINER_PYTORCH_CPU_INCLUDE_DIR),\
		-o /output/$(shell basename '$@') /work/$(shell basename '$<'))

$(CONTAINER_PYTORCH_GPU_BUILD_SENTINEL): $(CONTAINER_PYTORCH_GPU_DOCKERFILE) $(CONTAINER_PYTORCH_GPU_INCLUDE_FILES) $(CONTAINER_PYTORCH_GPU_SCRIPTS)
	$(call make_subdirectory,$(@D))
	$(call run_build_script,$(CONTAINER_PYTORCH_GPU_COMPONENT_NAME),$(CONTAINER_IMAGE_TAG),$(CONTAINER_BUILD_NUMBER))
	$(call save_sentinel_file,$(CONTAINER_PYTORCH_GPU_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_PYTORCH_GPU_PULL_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call pull_docker_images,$(CONTAINER_PYTORCH_GPU_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_PYTORCH_GPU_BUILD_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_PYTORCH_GPU_PUSH_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call push_docker_images,$(CONTAINER_PYTORCH_GPU_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_PYTORCH_GPU_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_PYTORCH_GPU_SCRIPTS): $(CONTAINER_PYTORCH_GPU_SHELLSCRIPTS_EXT) | $(CONTAINER_PYTORCH_GPU_INCLUDE_DIR)
	$(call run_argbash,\
		$(PROJECT_DIR)/$(PROJECT_SRC_SHELLSCRIPTS_DIR),\
		$(PROJECT_DIR)/$(CONTAINER_PYTORCH_GPU_INCLUDE_DIR),\
		-o /output/$(shell basename '$@') /work/$(shell basename '$<'))

$(CONTAINER_TENSORFLOW2_CPU_BUILD_SENTINEL): $(CONTAINER_TENSORFLOW2_CPU_DOCKERFILE) $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_FILES) $(CONTAINER_TENSORFLOW2_CPU_SCRIPTS)
	$(call make_subdirectory,$(@D))
	$(call run_build_script,$(CONTAINER_TENSORFLOW2_CPU_COMPONENT_NAME),$(CONTAINER_IMAGE_TAG),$(CONTAINER_BUILD_NUMBER))
	$(call save_sentinel_file,$(CONTAINER_TENSORFLOW2_CPU_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_TENSORFLOW2_CPU_PULL_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call pull_docker_images,$(CONTAINER_TENSORFLOW2_CPU_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_TENSORFLOW2_CPU_BUILD_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_TENSORFLOW2_CPU_PUSH_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call push_docker_images,$(CONTAINER_TENSORFLOW2_CPU_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_TENSORFLOW2_CPU_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_TENSORFLOW2_CPU_SCRIPTS): $(CONTAINER_TENSORFLOW2_CPU_SHELLSCRIPTS_EXT) | $(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR)
	$(call run_argbash,\
		$(PROJECT_DIR)/$(PROJECT_SRC_SHELLSCRIPTS_DIR),\
		$(PROJECT_DIR)/$(CONTAINER_TENSORFLOW2_CPU_INCLUDE_DIR),\
		-o /output/$(shell basename '$@') /work/$(shell basename '$<'))

$(CONTAINER_TENSORFLOW2_GPU_BUILD_SENTINEL): $(CONTAINER_TENSORFLOW2_GPU_DOCKERFILE) $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_FILES) $(CONTAINER_TENSORFLOW2_GPU_SCRIPTS)
	$(call make_subdirectory,$(@D))
	$(call run_build_script,$(CONTAINER_TENSORFLOW2_GPU_COMPONENT_NAME),$(CONTAINER_IMAGE_TAG),$(CONTAINER_BUILD_NUMBER))
	$(call save_sentinel_file,$(CONTAINER_TENSORFLOW2_GPU_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_TENSORFLOW2_GPU_PULL_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call pull_docker_images,$(CONTAINER_TENSORFLOW2_GPU_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_TENSORFLOW2_GPU_BUILD_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_TENSORFLOW2_GPU_PUSH_SENTINEL):
ifndef ARTIFACTORY_PREFIX
	$(error ARTIFACTORY_PREFIX must be defined.)
endif
	$(call make_subdirectory,$(@D))
	$(call push_docker_images,$(CONTAINER_TENSORFLOW2_GPU_IMAGE))
	$(call save_sentinel_file,$(CONTAINER_TENSORFLOW2_GPU_PULL_SENTINEL))
	$(call save_sentinel_file,$@)

$(CONTAINER_TENSORFLOW2_GPU_SCRIPTS): $(CONTAINER_TENSORFLOW2_GPU_SHELLSCRIPTS_EXT) | $(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR)
	$(call run_argbash,\
		$(PROJECT_DIR)/$(PROJECT_SRC_SHELLSCRIPTS_DIR),\
		$(PROJECT_DIR)/$(CONTAINER_TENSORFLOW2_GPU_INCLUDE_DIR),\
		-o /output/$(shell basename '$@') /work/$(shell basename '$<'))

$(EXAMPLES_TENSORFLOW_MNIST_SCRIPTS): $(EXAMPLES_TENSORFLOW_MNIST_SHELLSCRIPTS_EXT) | $(EXAMPLES_TENSORFLOW_MNIST_DIR)
	$(call run_argbash,\
		$(PROJECT_DIR)/$(EXAMPLES_TENSORFLOW_MNIST_DIR),\
		$(PROJECT_DIR)/$(EXAMPLES_TENSORFLOW_MNIST_DIR),\
		-o /output/$(shell basename '$@') /work/$(shell basename '$<'))

$(DOCS_SENTINEL): $(DOCS_FILES)
	$(call make_subdirectory,$(@D))
	$(call run_mkdocs,build -d $(DOCS_BUILD_DIR))
	$(call save_sentinel_file,$@)

$(GITLAB_PAGES_SENTINEL): $(GITLAB_PAGES_CI_FILE)
	$(call make_subdirectory,$(@D))
	$(call push_gitlab_pages,\
		$(GITLAB_PAGES_IMPORT_OPTS),\
		$(GITLAB_PAGES_BRANCH),\
		$(GITLAB_PAGES_BUILD_DIR))
	$(call save_sentinel_file,$@)

$(ISORT_CONFIG_FILE): $(CODE_SRC_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES)
	$(call run_seed_isort_config,)

$(LINTING_SENTINEL): $(CODE_SRC_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES)
	$(call make_subdirectory,$(@D))
	$(call run_flake8,)
	$(call save_sentinel_file,$@)

$(PRE_COMMIT_HOOKS_SENTINEL): $(PRE_COMMIT_CONFIG_FILE)
	$(call make_subdirectory,$(@D))
	$(call pre_commit_cmd,install --install-hooks)
	$(call pre_commit_cmd,install --hook-type commit-msg)
	$(call save_sentinel_file,$@)

$(TYPE_CHECK_SENTINEL): $(CODE_SRC_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES)
	$(call make_subdirectory,$(@D))
	$(call run_mypy,)
	$(call save_sentinel_file,$@)

$(TOX_SENTINEL): $(TOX_CONFIG_FILE) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES)
	$(call make_subdirectory,$(@D))
	$(call run_tox,)
	$(call save_sentinel_file,$@)

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars --QUIT-AT-EOF')
