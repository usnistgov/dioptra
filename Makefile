.PHONY: beautify build-all build-miniconda build-mlflow-tracking build-nginx build-postgres build-pytorch build-pytorch-cpu build-pytorch-gpu build-redis build-restapi build-sklearn build-sphinx build-tensorflow build-tensorflow-cpu build-tensorflow-gpu build-tox clean code-check code-pkg conda-env docs help hooks pull-mitre push-mitre tests tests-integration tests-unit tox
SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -O extglob -o pipefail -c
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

COMMA := ,

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = securing-ai-lab-components
PROJECT_VERSION = 0.0.0
PROJECT_PREFIX = securing-ai
PROJECT_BUILD_DIR = build
PROJECT_DOCS_DIR = docs
PROJECT_DOCKER_DIR = docker
PROJECT_SRC_DIR = src
PROJECT_SRC_MIGRATIONS_DIR = $(PROJECT_SRC_DIR)/migrations
PROJECT_SRC_MITRE_DIR = $(PROJECT_SRC_DIR)/mitre
PROJECT_SRC_SECURINGAI_DIR = $(PROJECT_SRC_MITRE_DIR)/securingai
PROJECT_SRC_SHELLSCRIPTS_DIR = $(PROJECT_SRC_DIR)/shellscript
PROJECT_TESTS_DIR = tests

BLACK = black
COPY = cp
DOCKER = docker
FIND = find
FLAKE8 = flake8
FLASK = flask
GIT = git
ISORT = isort
MV = mv
MYPY = mypy
PRE_COMMIT = pre-commit
PY ?= python3.8
PYTEST = pytest
RM = rm
TOX = tox

GITLAB_CI_FILE = .gitlab-ci.yml
MAKEFILE_FILE = Makefile
PRE_COMMIT_CONFIG_FILE = .pre-commit-config.yaml
SETUP_CFG_FILE = setup.cfg
TOX_CONFIG_FILE = tox.ini

CODE_PKG_NAME = mitre-securing-ai
CODE_PKG_VERSION = $(PROJECT_VERSION)
CODE_BUILD_DIR = dist
CODE_DOT_TOX_DIR = .tox
CODE_PIP_CACHE_DIR = .pip-cache
CODE_INTEGRATION_TESTS_DIR = $(PROJECT_TESTS_DIR)/integration
CODE_UNIT_TESTS_DIR = $(PROJECT_TESTS_DIR)/unit
CODE_TOX_PY37_PIP_CACHE_DIR = $(CODE_DOT_TOX_DIR)/pip-cache-py37
CODE_TOX_PY38_PIP_CACHE_DIR = $(CODE_DOT_TOX_DIR)/pip-cache-py38
CODE_SRC_FILES := $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/mlflow_plugins/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/pyplugs/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/restapi/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/restapi/*/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/restapi/*/*/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/rq/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/rq/*/*.py)
CODE_DB_MIGRATIONS_FILES :=\
    $(PROJECT_SRC_MIGRATIONS_DIR)/alembic.ini\
    $(PROJECT_SRC_MIGRATIONS_DIR)/env.py\
    $(PROJECT_SRC_MIGRATIONS_DIR)/README\
    $(PROJECT_SRC_MIGRATIONS_DIR)/script.py.mako
CODE_DB_MIGRATIONS_FILES += $(wildcard $(PROJECT_SRC_MIGRATIONS_DIR)/versions/*.py)
CODE_INTEGRATION_TESTS_FILES := $(wildcard $(CODE_INTEGRATION_TESTS_DIR)/*.py)
CODE_INTEGRATION_TESTS_FILES += $(wildcard $(CODE_INTEGRATION_TESTS_DIR)/*/*.py)
CODE_INTEGRATION_TESTS_FILES += $(wildcard $(CODE_INTEGRATION_TESTS_DIR)/*/*/*.py)
CODE_INTEGRATION_TESTS_FILES += $(wildcard $(CODE_INTEGRATION_TESTS_DIR)/*/*/*/*.py)
CODE_UNIT_TESTS_FILES := $(wildcard $(CODE_UNIT_TESTS_DIR)/*.py)
CODE_UNIT_TESTS_FILES += $(wildcard $(CODE_UNIT_TESTS_DIR)/*/*.py)
CODE_UNIT_TESTS_FILES += $(wildcard $(CODE_UNIT_TESTS_DIR)/*/*/*.py)
CODE_UNIT_TESTS_FILES += $(wildcard $(CODE_UNIT_TESTS_DIR)/*/*/*/*.py)
CODE_PACKAGING_FILES =\
    $(DOCS_FILES)\
    $(SETUP_CFG_FILE)\
    $(TOX_CONFIG_FILE)\
    LICENSE\
    MANIFEST.in\
    pyproject.toml
CODE_DISTRIBUTION_FILES =\
    $(CODE_BUILD_DIR)/$(CODE_PKG_NAME)-$(CODE_PKG_VERSION).tar.gz\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl

CONTAINER_OS_VERSION = focal
CONTAINER_OS_VERSION_NUMBER = 20.04
CONTAINER_OS_BUILD_NUMBER = 20201106
CONTAINER_BUILD_NUMBER = 3
CONTAINER_IMAGE_TAG = $(PROJECT_VERSION)-$(CONTAINER_BUILD_NUMBER)
CONTAINER_IBM_ART_VERSION = 1.5.0
CONTAINER_MINICONDA_VERSION = 4.9.2
CONTAINER_SPHINX_VERSION = 3.3.1
CONTAINER_MLFLOW_VERSION = 1.12.1
CONTAINER_PREFECT_VERSION = 0.13.19
CONTAINER_PYTORCH_VERSION = 1.7.1
CONTAINER_SKLEARN_VERSION = 0.22.2
CONTAINER_TENSORFLOW2_VERSION = 2.1.0

DOCS_BUILD_DIR = $(PROJECT_DOCS_DIR)/build
DOCS_SOURCE_DIR = $(PROJECT_DOCS_DIR)/source
DOCS_FILES := $(wildcard $(DOCS_SOURCE_DIR)/*.py)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/architecture/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/dev-guide/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/overview/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/pyplugs/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/restapi/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/sdk/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/_static/*)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/_templates/*)

PIP :=
ifeq ($(DETECTED_OS),Darwin)
    PIP += CFLAGS="-stdlib=libc++" pip
else
    PIP += pip
endif
CONDA = conda
CONDA_CHANNELS = -c defaults
CONDA_ENV_BASE := python=3.8 pip setuptools wheel
ifeq ($(DETECTED_OS),Darwin)
    CONDA_ENV_BASE +=
endif
CONDA_ENV_FILE = environment.yml
CONDA_ENV_NAME = $(PROJECT_NAME)
CONDA_ENV_PIP =

ARTIFACTORY_PREFIX = artifacts.mitre.org:8200
ARTIFACTORY_UNTRUSTED_PREFIX = $(ARTIFACTORY_PREFIX)/untrusted-mitrewide-overwritable

CONTAINER_MINICONDA_BASE_INCLUDE_FILES =\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/aws-config\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/bash.bashrc\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/dot-condarc
CONTAINER_MINICONDA_BASE_SCRIPTS =\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/fix-permissions.sh\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/install-python-modules.sh\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/s3-cp.sh\
    $(CONTAINER_MINICONDA_BASE_INCLUDE_DIR)/unpack-archive.sh
CONTAINER_MLFLOW_TRACKING_INCLUDE_FILES =
CONTAINER_MLFLOW_TRACKING_SCRIPTS =\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/entrypoint-mlflow-tracking.sh\
    $(CONTAINER_MLFLOW_TRACKING_INCLUDE_DIR)/s3-mb.sh
CONTAINER_NGINX_INCLUDE_FILES =\
    $(CONTAINER_NGINX_INCLUDE_DIR)/default.conf\
    $(CONTAINER_NGINX_INCLUDE_DIR)/nginx.conf
CONTAINER_NGINX_SCRIPTS =\
    $(CONTAINER_NGINX_INCLUDE_DIR)/entrypoint-nginx.sh\
    $(CONTAINER_NGINX_INCLUDE_DIR)/secure-container.sh
CONTAINER_RESTAPI_INCLUDE_FILES =\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/gunicorn.conf.py\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/uwsgi.ini\
    $(CODE_DB_MIGRATIONS_FILES)\
    wsgi.py
CONTAINER_RESTAPI_SCRIPTS =\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/entrypoint-restapi.sh\
    $(CONTAINER_RESTAPI_INCLUDE_DIR)/secure-container.sh
CONTAINER_SKLEARN_INCLUDE_FILES :=
CONTAINER_SKLEARN_SCRIPTS =\
    $(CONTAINER_SKLEARN_INCLUDE_DIR)/entrypoint-sklearn.sh\
    $(CONTAINER_SKLEARN_INCLUDE_DIR)/restrict-network-access.sh\
    $(CONTAINER_SKLEARN_INCLUDE_DIR)/run-mlflow-job.sh\
    $(CONTAINER_SKLEARN_INCLUDE_DIR)/secure-container.sh
CONTAINER_SPHINX_INCLUDE_FILES =
CONTAINER_SPHINX_SCRIPTS =
CONTAINER_POSTGRES_INCLUDE_FILES =
CONTAINER_POSTGRES_SCRIPTS =
CONTAINER_REDIS_INCLUDE_FILES =
CONTAINER_REDIS_SCRIPTS =
CONTAINER_PYTORCH_CPU_INCLUDE_FILES =\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl
CONTAINER_PYTORCH_CPU_SCRIPTS =
CONTAINER_PYTORCH_GPU_INCLUDE_FILES =\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl
CONTAINER_PYTORCH_GPU_SCRIPTS =
CONTAINER_TENSORFLOW2_CPU_INCLUDE_FILES =\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl
CONTAINER_TENSORFLOW2_CPU_SCRIPTS =
CONTAINER_TENSORFLOW2_GPU_INCLUDE_FILES =\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl
CONTAINER_TENSORFLOW2_GPU_SCRIPTS =
CONTAINER_TOX_PY37_INCLUDE_FILES =
CONTAINER_TOX_PY37_SCRIPTS =
CONTAINER_TOX_PY38_INCLUDE_FILES =
CONTAINER_TOX_PY38_SCRIPTS =

BEAUTIFY_SENTINEL = $(PROJECT_BUILD_DIR)/.beautify.sentinel
CODE_INTEGRATION_TESTS_SENTINEL = $(PROJECT_BUILD_DIR)/.integration-tests.sentinel
CODE_UNIT_TESTS_SENTINEL = $(PROJECT_BUILD_DIR)/.unit-tests.sentinel
CONDA_CREATE_SENTINEL = $(PROJECT_BUILD_DIR)/.conda-create.sentinel
CONDA_UPDATE_SENTINEL = $(PROJECT_BUILD_DIR)/.conda-update.sentinel
CONDA_ENV_DEV_INSTALL_SENTINEL = $(PROJECT_BUILD_DIR)/.conda-env-dev-install.sentinel
CONDA_ENV_PIP_INSTALL_SENTINEL = $(PROJECT_BUILD_DIR)/.conda-env-pip-install.sentinel
CONTAINER_PULL_SENTINELS =
CONTAINER_PUSH_SENTINELS =
DOCS_SENTINEL = $(PROJECT_BUILD_DIR)/.docs.sentinel
LINTING_SENTINEL = $(PROJECT_BUILD_DIR)/.linting.sentinel
PRE_COMMIT_HOOKS_SENTINEL = $(PROJECT_BUILD_DIR)/.pre-commit-hooks.sentinel
TOX_PY37_SENTINEL = $(PROJECT_BUILD_DIR)/.tox-py37.sentinel
TOX_PY38_SENTINEL = $(PROJECT_BUILD_DIR)/.tox-py38.sentinel
TYPE_CHECK_SENTINEL = $(PROJECT_BUILD_DIR)/.type-check.sentinel

#################################################################################
# FUNCTIONS                                                                     #
#################################################################################

define cleanup
$(FIND) . \( -name "__pycache__" -and -not -path "./.tox*" \) -type d -exec $(RM) -rf {} +
$(FIND) . \( -name "*.py[co]" -and -not -path "./.tox*" \) -type f -exec $(RM) -rf {} +
$(FIND) . -name ".ipynb_checkpoints" -type d -exec $(RM) -rf {} +
$(RM) -rf $(PROJECT_DIR)/.coverage
$(RM) -rf $(PROJECT_DIR)/.pip-cache
$(RM) -rf $(PROJECT_DIR)/coverage
$(RM) -rf $(PROJECT_DIR)/dist
$(RM) -rf $(PROJECT_DIR)/htmlcov
$(RM) -rf $(PROJECT_DIR)/mlruns
$(RM) -rf $(PROJECT_BUILD_DIR)/bdist*
$(RM) -rf $(PROJECT_BUILD_DIR)/docs
$(RM) -rf $(PROJECT_BUILD_DIR)/lib
$(RM) -rf $(PROJECT_DOCS_DIR)/build/*
endef

define create_conda_env
bash -lc "\
$(CONDA) create -n $(CONDA_ENV_NAME) $(CONDA_CHANNELS) -y $(CONDA_ENV_BASE)"
endef

define docker_image_tag
$(call run_docker,tag $(strip $(1)) $(strip $(2)))
endef

define make_subdirectory
mkdir -p "$(strip $(1))"
endef

define get_host_user_id
$(shell id -u)
endef

define package_code
$(call run_docker,\
    run\
    -t\
    --rm\
    -e PIP_CACHE_DIR=/work/.pip-cache\
    -u $(strip $(call get_host_user_id)):100\
    -v $(PROJECT_DIR):/work\
    --entrypoint ""\
    $(CONTAINER_MINICONDA_BASE_IMAGE)\
    bash -ic "python -m build -sw")
endef

define pull_docker_images
@$(foreach image,$(1),\
    echo "Pulling image $(image)";\
    echo "==========================================";\
    $(DOCKER) pull $(strip $(2))/$(image) || exit 1;\
    $(DOCKER) tag $(strip $(2))/$(image) $(image) || exit 1;\
    $(DOCKER) rmi $(strip $(2))/$(image) || exit 1;\
    echo "";)
endef

define push_docker_images
@$(foreach image,$(1),\
    echo "Pushing image $(image)";\
    echo "==========================================";\
    $(DOCKER) tag $(image) $(strip $(2))/$(image) || exit 1;\
    $(DOCKER) push $(strip $(2))/$(image) || exit 1;\
    $(DOCKER) rmi $(strip $(2))/$(image) || exit 1;\
    echo "";)
endef

define pre_commit_cmd
$(PRE_COMMIT) $(1)
endef

define run_argbash
$(call run_docker,\
    run\
    -t\
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
PREFECT_VERSION=$(CONTAINER_PREFECT_VERSION)\
PYTORCH_VERSION=$(CONTAINER_PYTORCH_VERSION)\
SKLEARN_VERSION=$(CONTAINER_SKLEARN_VERSION)\
SPHINX_VERSION=$(CONTAINER_SPHINX_VERSION)\
TENSORFLOW2_VERSION=$(CONTAINER_TENSORFLOW2_VERSION)\
docker/build.sh
endef

define run_docker
$(DOCKER) $(1)
endef

define run_flake8
$(FLAKE8) $(1)
endef

define run_isort
$(ISORT) $(1)
endef

define run_mypy
$(MYPY) $(1)
endef

define run_pip_install
bash -lc "\
$(CONDA) activate $(CONDA_ENV_NAME) &&\
$(PIP) install $(1) &&\
$(CONDA) deactivate"
endef

define run_pytest
$(PYTEST) $(1)
endef

define run_python_black
$(BLACK) $(1)
endef

define run_sphinx_build
$(call run_docker,\
    run\
    -t\
    --rm\
    -v $(PROJECT_DIR):/docs\
    $(CONTAINER_SPHINX_IMAGE)\
    sphinx-build\
    -b html\
    $(strip $(1))\
    $(strip $(2)))
endef

define run_tox_py37
$(call run_docker,\
    run\
    -t\
    --rm\
    -e PIP_CACHE_DIR=/work/.tox/pip-cache-py37\
    -u $(strip $(call get_host_user_id)):100\
    -v $(PROJECT_DIR):/work\
    --entrypoint ""\
    --workdir /work\
    $(CONTAINER_TOX_PY37_IMAGE)\
    $(TOX))
endef

define run_tox_py38
$(call run_docker,\
    run\
    -t\
    --rm\
    -e PIP_CACHE_DIR=/work/.tox/pip-cache-py38\
    -u $(strip $(call get_host_user_id)):100\
    -v $(PROJECT_DIR):/work\
    --entrypoint ""\
    --workdir /work\
    $(CONTAINER_TOX_PY38_IMAGE)\
    $(TOX))
endef

define save_sentinel_file
@touch $(1)
endef

define split_string_and_get_word
$(word $3,$(subst $2, ,$1))
endef

define string_to_lower
$(shell echo $(1) | tr '[:upper:]' '[:lower:]')
endef

define string_to_upper
$(shell echo $(1) | tr '[:lower:]' '[:upper:]')
endef

define update_conda_env
bash -lc "\
$(CONDA) env update --file $(CONDA_ENV_FILE)"
endef

define build_docker_image_recipe
$(strip $(1)): $(strip $(2)) | $$(PROJECT_BUILD_DIR)
	$(call run_build_script,$(3),$(4),$(5))
	$(call save_sentinel_file,$(6))
	$(call save_sentinel_file,$$@)
endef

define set_latest_tag_docker_image_recipe
$(strip $(1)): $(strip $(2)) | $$(PROJECT_BUILD_DIR)
	$(call docker_image_tag,$(3),$(4))
	$(call save_sentinel_file,$$@)
endef

define pull_docker_image_recipe
$(strip $(1)): | $$(PROJECT_BUILD_DIR)
	$(call pull_docker_images,$(2),$(ARTIFACTORY_PREFIX))
	$(call save_sentinel_file,$(3))
	$(call save_sentinel_file,$$@)
endef

define pull_latest_docker_image_recipe
$(strip $(1)): | $$(PROJECT_BUILD_DIR)
	$(call pull_docker_images,$(2),$(ARTIFACTORY_UNTRUSTED_PREFIX))
	$(call save_sentinel_file,$(3))
	$(call save_sentinel_file,$$@)
endef

define push_docker_image_recipe
$(strip $(1)): | $$(PROJECT_BUILD_DIR)
	$(call push_docker_images,$(2),$(ARTIFACTORY_PREFIX))
	$(call save_sentinel_file,$(3))
	$(call save_sentinel_file,$$@)
endef

define push_latest_docker_image_recipe
$(strip $(1)): | $$(PROJECT_BUILD_DIR)
	$(call push_docker_images,$(2),$(ARTIFACTORY_UNTRUSTED_PREFIX))
	$(call save_sentinel_file,$(3))
	$(call save_sentinel_file,$$@)
endef

define generate_docker_image_shellscripts_recipe
$(strip $(1)):

$(strip $(2))/%.sh: $$(PROJECT_SRC_SHELLSCRIPTS_DIR)/%.m4
	$(call run_argbash,\
		$$(PROJECT_DIR)/$$(PROJECT_SRC_SHELLSCRIPTS_DIR),\
		$$(PROJECT_DIR)/$(strip $(2)),\
		-o /output/$$(shell basename '$$@') /work/$$(shell basename '$$<'))
endef

define define_docker_image_sentinel_vars
CONTAINER_$(strip $(1))_COMPONENT_NAME = $(strip $(3))
CONTAINER_$(strip $(1))_IMAGE = $$(PROJECT_PREFIX)/$$(CONTAINER_$(strip $(1))_COMPONENT_NAME):$$($(strip $(2)))
CONTAINER_$(strip $(1))_IMAGE_LATEST = $$(PROJECT_PREFIX)/$$(CONTAINER_$(strip $(1))_COMPONENT_NAME):latest
CONTAINER_$(strip $(1))_DIR = $$(PROJECT_DOCKER_DIR)/$$(CONTAINER_$(strip $(1))_COMPONENT_NAME)
CONTAINER_$(strip $(1))_INCLUDE_DIR = $$(CONTAINER_$(strip $(1))_DIR)/include/etc/$$(PROJECT_PREFIX)/docker
CONTAINER_$(strip $(1))_DOCKERFILE = $$(CONTAINER_$(strip $(1))_DIR)/Dockerfile
CONTAINER_$(strip $(1))_BUILD_SENTINEL = $$(PROJECT_BUILD_DIR)/.docker-image-$$(CONTAINER_$(strip $(1))_COMPONENT_NAME)-tag-$$($(strip $(2))).sentinel
CONTAINER_$(strip $(1))_BUILD_LATEST_SENTINEL = $$(PROJECT_BUILD_DIR)/.docker-image-$$(CONTAINER_$(strip $(1))_COMPONENT_NAME)-tag-latest.sentinel
CONTAINER_$(strip $(1))_PULL_SENTINEL = $$(PROJECT_BUILD_DIR)/.docker-image-$$(CONTAINER_$(strip $(1))_COMPONENT_NAME)-pulled-tag-$$($(strip $(2))).sentinel
CONTAINER_$(strip $(1))_PULL_LATEST_SENTINEL = $$(PROJECT_BUILD_DIR)/.docker-image-$$(CONTAINER_$(strip $(1))_COMPONENT_NAME)-pulled-tag-latest.sentinel
CONTAINER_$(strip $(1))_PUSH_SENTINEL = $$(PROJECT_BUILD_DIR)/.docker-image-$$(CONTAINER_$(strip $(1))_COMPONENT_NAME)-pushed-tag-$$($(strip $(2))).sentinel
CONTAINER_$(strip $(1))_PUSH_LATEST_SENTINEL = $$(PROJECT_BUILD_DIR)/.docker-image-$$(CONTAINER_$(strip $(1))_COMPONENT_NAME)-pushed-tag-latest.sentinel
CONTAINER_PULL_SENTINELS += $$(CONTAINER_$(strip $(1))_PULL_SENTINEL)
CONTAINER_PULL_SENTINELS += $$(CONTAINER_$(strip $(1))_PULL_LATEST_SENTINEL)
CONTAINER_PUSH_SENTINELS += $$(CONTAINER_$(strip $(1))_PUSH_SENTINEL)
CONTAINER_PUSH_SENTINELS += $$(CONTAINER_$(strip $(1))_PUSH_LATEST_SENTINEL)
endef

define generate_docker_image_pipeline
$(eval $(call build_docker_image_recipe,$(1),$(strip $(2) $(12)),$(5),$(6),$(7),$(8)))
$(eval $(call pull_docker_image_recipe,$(8),$(3),$(1)))
$(eval $(call pull_latest_docker_image_recipe,$(9),$(4),$(14)))
$(eval $(call push_docker_image_recipe,$(10),$(3),$(8)))
$(eval $(call push_latest_docker_image_recipe,$(11),$(4),$(9)))
$(eval $(call set_latest_tag_docker_image_recipe,$(14),$(1),$(3),$(4)))
$(eval $(call generate_docker_image_shellscripts_recipe,$(12),$(13)))
endef

define generate_full_docker_image_vars
$(eval $(call define_docker_image_sentinel_vars,$(1),$(2),$(3)))
endef

define generate_full_docker_image_recipe
$(eval $(call generate_docker_image_pipeline,\
	$$(CONTAINER_$(1)_BUILD_SENTINEL),\
	$$($(2)) $$(CONTAINER_$(1)_DOCKERFILE) $$(CONTAINER_$(1)_INCLUDE_FILES),\
	$$(CONTAINER_$(1)_IMAGE),\
	$$(CONTAINER_$(1)_IMAGE_LATEST),\
	$$(CONTAINER_$(1)_COMPONENT_NAME),\
	$$($(3)),\
	$$($(4)),\
	$$(CONTAINER_$(1)_PULL_SENTINEL),\
	$$(CONTAINER_$(1)_PULL_LATEST_SENTINEL),\
	$$(CONTAINER_$(1)_PUSH_SENTINEL),\
	$$(CONTAINER_$(1)_PUSH_LATEST_SENTINEL),\
	$$(CONTAINER_$(1)_SCRIPTS),\
	$$(CONTAINER_$(1)_INCLUDE_DIR),\
	$$(CONTAINER_$(1)_BUILD_LATEST_SENTINEL)))
endef

#################################################################################
# AUTO-GENERATED GLOBALS                                                        #
#################################################################################

$(call generate_full_docker_image_vars,MINICONDA_BASE,CONTAINER_IMAGE_TAG,miniconda-base)
$(call generate_full_docker_image_vars,SPHINX,CONTAINER_IMAGE_TAG,sphinx)
$(call generate_full_docker_image_vars,MLFLOW_TRACKING,CONTAINER_IMAGE_TAG,mlflow-tracking)
$(call generate_full_docker_image_vars,NGINX,CONTAINER_IMAGE_TAG,nginx)
$(call generate_full_docker_image_vars,POSTGRES,CONTAINER_IMAGE_TAG,postgres)
$(call generate_full_docker_image_vars,REDIS,CONTAINER_IMAGE_TAG,redis)
$(call generate_full_docker_image_vars,RESTAPI,CONTAINER_IMAGE_TAG,restapi)
$(call generate_full_docker_image_vars,SKLEARN,CONTAINER_IMAGE_TAG,sklearn)
$(call generate_full_docker_image_vars,PYTORCH_CPU,CONTAINER_IMAGE_TAG,pytorch-cpu)
$(call generate_full_docker_image_vars,PYTORCH_GPU,CONTAINER_IMAGE_TAG,pytorch-gpu)
$(call generate_full_docker_image_vars,TENSORFLOW2_CPU,CONTAINER_IMAGE_TAG,tensorflow2-cpu)
$(call generate_full_docker_image_vars,TENSORFLOW2_GPU,CONTAINER_IMAGE_TAG,tensorflow2-gpu)
$(call generate_full_docker_image_vars,TOX_PY37,CONTAINER_IMAGE_TAG,tox-py37)
$(call generate_full_docker_image_vars,TOX_PY38,CONTAINER_IMAGE_TAG,tox-py38)

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Reformat code
beautify: $(BEAUTIFY_SENTINEL)

## Build all Docker images in project
build-all: build-sphinx build-tox build-nginx build-postgres build-redis build-miniconda build-mlflow-tracking build-restapi build-sklearn build-pytorch build-tensorflow

## Build the base Miniconda Docker image
build-miniconda: $(CONTAINER_MINICONDA_BASE_BUILD_LATEST_SENTINEL)

## Build the MLFlow Tracking Docker image
build-mlflow-tracking: $(CONTAINER_MLFLOW_TRACKING_BUILD_LATEST_SENTINEL)

## Build the nginx Docker image
build-nginx: $(CONTAINER_NGINX_BUILD_LATEST_SENTINEL)

## Build the postgres Docker image
build-postgres: $(CONTAINER_POSTGRES_BUILD_LATEST_SENTINEL)

## Build the PyTorch Docker images
build-pytorch: build-pytorch-cpu build-pytorch-gpu

## Build the PyTorch (CPU) Docker image
build-pytorch-cpu: $(CONTAINER_PYTORCH_CPU_BUILD_LATEST_SENTINEL)

## Build the PyTorch (GPU) Docker image
build-pytorch-gpu: $(CONTAINER_PYTORCH_GPU_BUILD_LATEST_SENTINEL)

## Build the Redis Docker image
build-redis: $(CONTAINER_REDIS_BUILD_LATEST_SENTINEL)

## Build the restapi Docker image
build-restapi: $(CONTAINER_RESTAPI_BUILD_LATEST_SENTINEL)

## Build the scikit-learn Docker image
build-sklearn: $(CONTAINER_SKLEARN_BUILD_LATEST_SENTINEL)

## Build the Sphinx image
build-sphinx: $(CONTAINER_SPHINX_BUILD_LATEST_SENTINEL)

## Build the Tensorflow Docker images
build-tensorflow: build-tensorflow-cpu build-tensorflow-gpu

## Build the Tensorflow (CPU) Docker image
build-tensorflow-cpu: $(CONTAINER_TENSORFLOW2_CPU_BUILD_LATEST_SENTINEL)

## Build the Tensorflow (GPU) Docker image
build-tensorflow-gpu: $(CONTAINER_TENSORFLOW2_GPU_BUILD_LATEST_SENTINEL)

## Build the Tox Docker images
build-tox: $(CONTAINER_TOX_PY37_BUILD_LATEST_SENTINEL) $(CONTAINER_TOX_PY38_BUILD_LATEST_SENTINEL)

## Remove temporary files
clean: ; $(call cleanup)

## Lint and type check the source code
code-check: $(LINTING_SENTINEL) $(TYPE_CHECK_SENTINEL)

## Package source code for distribution
code-pkg: $(CODE_DISTRIBUTION_FILES)

## Update conda-based virtual environment
conda-env: $(CONDA_CREATE_SENTINEL) $(CONDA_UPDATE_SENTINEL) $(CONDA_ENV_PIP_INSTALL_SENTINEL) $(CONDA_ENV_DEV_INSTALL_SENTINEL)

## Build project documentation
docs: $(DOCS_SENTINEL)

## Install pre-commit hooks
hooks: $(PRE_COMMIT_HOOKS_SENTINEL)

## Pull latest docker images from the MITRE artifactory and retag
pull-mitre: $(CONTAINER_PULL_SENTINELS)

## Push docker images to the MITRE artifactory
push-mitre: $(CONTAINER_PUSH_SENTINELS)

## Run all tests
tests: tests-unit tests-integration

## Run integration tests
tests-integration: $(CODE_INTEGRATION_TESTS_SENTINEL)

## Run unit tests
tests-unit: $(CODE_UNIT_TESTS_SENTINEL)

## Run all tests using tox
tox: $(TOX_PY38_SENTINEL)

#################################################################################
# PROJECT BUILD RECIPES                                                         #
#################################################################################

$(PROJECT_BUILD_DIR): ; $(call make_subdirectory,$@)
$(CODE_PIP_CACHE_DIR): ; $(call make_subdirectory,$@)
$(CODE_TOX_PY37_PIP_CACHE_DIR): ; $(call make_subdirectory,$@)
$(CODE_TOX_PY38_PIP_CACHE_DIR): ; $(call make_subdirectory,$@)

$(BEAUTIFY_SENTINEL): $(CODE_SRC_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_python_black,$(PROJECT_SRC_SECURINGAI_DIR) $(PROJECT_TESTS_DIR))
	$(call run_isort,$(PROJECT_SRC_SECURINGAI_DIR))
	$(call run_isort,$(PROJECT_TESTS_DIR))
	$(call save_sentinel_file,$@)

$(CODE_INTEGRATION_TESTS_SENTINEL): $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR)
ifneq ($(strip $(CODE_INTEGRATION_TESTS_FILES)),)
	$(call run_pytest,$(CODE_INTEGRATION_TESTS_DIR))
endif
	$(call save_sentinel_file,$@)

$(CODE_UNIT_TESTS_SENTINEL): $(CODE_UNIT_TESTS_FILES) | $(PROJECT_BUILD_DIR)
ifneq ($(strip $(CODE_UNIT_TESTS_FILES)),)
	$(call run_pytest, $(CODE_UNIT_TESTS_DIR))
endif
	$(call save_sentinel_file,$@)

$(CODE_DISTRIBUTION_FILES): $(CONTAINER_MINICONDA_BASE_BUILD_SENTINEL) $(CODE_PACKAGING_FILES) $(CODE_SRC_FILES) $(DOCS_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR) $(CODE_PIP_CACHE_DIR)
	$(call package_code,$(CODE_BUILD_DIR))
	@echo ""
	@echo "$(CODE_PKG_NAME) packaged for distribution in $(CODE_BUILD_DIR)"

$(CONDA_CREATE_SENTINEL): | $(PROJECT_BUILD_DIR)
	$(call create_conda_env)
	$(call save_sentinel_file,$@)

$(CONDA_UPDATE_SENTINEL): $(CONDA_ENV_FILE) | $(PROJECT_BUILD_DIR)
	$(call update_conda_env)
	$(call save_sentinel_file,$@)

$(CONDA_ENV_PIP_INSTALL_SENTINEL): $(MAKEFILE_FILE) | $(PROJECT_BUILD_DIR)
ifdef CONDA_ENV_PIP
	$(call run_pip_install,$(subst ",,$(CONDA_ENV_PIP)))
endif
	$(call save_sentinel_file,$@)

$(CONDA_ENV_DEV_INSTALL_SENTINEL): $(MAKEFILE_FILE) | $(PROJECT_BUILD_DIR)
	$(call run_pip_install,-e .)
	$(call save_sentinel_file,$@)

$(DOCS_SENTINEL): $(CONTAINER_SPHINX_BUILD_LATEST_SENTINEL) $(DOCS_FILES) | $(PROJECT_BUILD_DIR)
	@$(RM) -rf $(DOCS_BUILD_DIR)
	$(call run_sphinx_build,$(DOCS_SOURCE_DIR),$(DOCS_BUILD_DIR))
	@$(RM) -rf $(PROJECT_DOCS_DIR)/mlruns
	$(call save_sentinel_file,$@)

$(LINTING_SENTINEL): $(CODE_SRC_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_flake8,$(PROJECT_SRC_SECURINGAI_DIR) $(PROJECT_TESTS_DIR))
	$(call save_sentinel_file,$@)

$(PRE_COMMIT_HOOKS_SENTINEL): $(PRE_COMMIT_CONFIG_FILE) | $(PROJECT_BUILD_DIR)
	$(call pre_commit_cmd,install --install-hooks)
	$(call pre_commit_cmd,install --hook-type commit-msg)
	$(call save_sentinel_file,$@)

$(TYPE_CHECK_SENTINEL): $(CODE_SRC_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_mypy,$(PROJECT_SRC_SECURINGAI_DIR) $(PROJECT_TESTS_DIR))
	$(call save_sentinel_file,$@)

$(TOX_PY37_SENTINEL): $(CONTAINER_TOX_PY37_BUILD_LATEST_SENTINEL) $(TOX_CONFIG_FILE) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR) $(CODE_TOX_PY37_PIP_CACHE_DIR)
	$(call run_tox_py37)
	$(call save_sentinel_file,$@)

$(TOX_PY38_SENTINEL): $(CONTAINER_TOX_PY38_BUILD_LATEST_SENTINEL) $(TOX_CONFIG_FILE) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR) $(CODE_TOX_PY38_PIP_CACHE_DIR)
	$(call run_tox_py38)
	$(call save_sentinel_file,$@)

#################################################################################
# AUTO-GENERATED PROJECT BUILD RECEIPES                                         #
#################################################################################

$(call generate_full_docker_image_recipe,MINICONDA_BASE,,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,SPHINX,,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,MLFLOW_TRACKING,CONTAINER_MINICONDA_BASE_BUILD_SENTINEL,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,NGINX,,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,POSTGRES,,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,REDIS,,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,RESTAPI,CONTAINER_MINICONDA_BASE_BUILD_SENTINEL,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,SKLEARN,CONTAINER_MINICONDA_BASE_BUILD_SENTINEL,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,PYTORCH_CPU,CONTAINER_SKLEARN_BUILD_SENTINEL,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,PYTORCH_GPU,CONTAINER_SKLEARN_BUILD_SENTINEL,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,TENSORFLOW2_CPU,CONTAINER_SKLEARN_BUILD_SENTINEL,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,TENSORFLOW2_GPU,CONTAINER_SKLEARN_BUILD_SENTINEL,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,TOX_PY37,,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)
$(call generate_full_docker_image_recipe,TOX_PY38,,CONTAINER_IMAGE_TAG,CONTAINER_BUILD_NUMBER)

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
