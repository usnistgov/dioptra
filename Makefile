.PHONY: beautify build-all build-ci build-lab build-mlflow-tracking build-nginx build-python-build build-pytorch build-pytorch-cpu build-pytorch-gpu build-restapi build-sphinx build-tensorflow build-tensorflow-cpu build-tensorflow-gpu build-tox ci-deps clean code-check code-pkg conda-env docker-deps docs help hooks pull-latest pull-latest-ci pull-latest-hub pull-latest-lab tag-latest-ci tag-latest-lab tests tests-integration tests-unit tox
SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -O extglob -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

#################################################################################
# GLOBALS                                                                       #
#################################################################################

include container-vars.mk
include version-vars.mk

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
PROJECT_PREFIX = securing-ai
PROJECT_BUILD_DIR = build
PROJECT_CI_DIR = ci
PROJECT_DOCS_DIR = docs
PROJECT_DOCKER_DIR = docker
PROJECT_DOCKER_SRC_DIR = $(PROJECT_DOCKER_DIR)/src
PROJECT_DOCKER_CONDA_ENV_DIR = $(PROJECT_DOCKER_SRC_DIR)/conda-env
PROJECT_DOCKER_SHELLSCRIPTS_DIR = $(PROJECT_DOCKER_SRC_DIR)/shellscripts
PROJECT_SRC_DIR = src
PROJECT_SRC_MIGRATIONS_DIR = $(PROJECT_SRC_DIR)/migrations
PROJECT_SRC_MITRE_DIR = $(PROJECT_SRC_DIR)/mitre
PROJECT_SRC_SECURINGAI_DIR = $(PROJECT_SRC_MITRE_DIR)/securingai
PROJECT_TASK_PLUGINS_DIR = task-plugins
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
PYTEST = $(PY) -m pytest
RM = rm
TOX = tox

CI_VERSION_VARS_YML = $(PROJECT_CI_DIR)/gitlab-ci-version-vars.yml
CONTAINER_VARS_FILE = container-vars.mk
GITLAB_CI_FILE = .gitlab-ci.yml
MAKEFILE_FILE = Makefile
PRE_COMMIT_CONFIG_FILE = .pre-commit-config.yaml
SETUP_CFG_FILE = setup.cfg
TOX_CONFIG_FILE = tox.ini
VERSION_VARS_FILE = version-vars.mk

CODE_PKG_NAME = mitre-securing-ai
CODE_BUILD_DIR = dist
CODE_DOT_TOX_DIR = .tox
CODE_PIP_CACHE_DIR = .pip-cache
CODE_INTEGRATION_TESTS_DIR = $(PROJECT_TESTS_DIR)/integration
CODE_SECURINGAI_BUILTINS_DIR = $(PROJECT_TASK_PLUGINS_DIR)/securingai_builtins
CODE_UNIT_TESTS_DIR = $(PROJECT_TESTS_DIR)/unit
CODE_TOX_PY37_PIP_CACHE_DIR = $(CODE_DOT_TOX_DIR)/pip-cache-py37
CODE_TOX_PY38_PIP_CACHE_DIR = $(CODE_DOT_TOX_DIR)/pip-cache-py38
CODE_SRC_FILES := $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/generics_plugins/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/generics_plugins/*/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/mlflow_plugins/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/pyplugs/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/restapi/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/restapi/*/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/restapi/*/*/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/rq/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/rq/*/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/sdk/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/sdk/*/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIR)/mitre/securingai/sdk/*/*/*.py)
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
CODE_TASK_PLUGINS_FILES := $(wildcard $(CODE_SECURINGAI_BUILTINS_DIR)/*.py)
CODE_TASK_PLUGINS_FILES += $(wildcard $(CODE_SECURINGAI_BUILTINS_DIR)/*/*.py)
CODE_TASK_PLUGINS_FILES += $(wildcard $(CODE_SECURINGAI_BUILTINS_DIR)/*/*/*.py)
CODE_TASK_PLUGINS_FILES += $(wildcard $(CODE_SECURINGAI_BUILTINS_DIR)/*/*/*/*.py)
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

DOCS_BUILD_DIR = $(PROJECT_DOCS_DIR)/build
DOCS_SOURCE_DIR = $(PROJECT_DOCS_DIR)/source
DOCS_FILES := $(wildcard $(DOCS_SOURCE_DIR)/*.py)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/deployment-guide/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/deployment-guide/*/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/dev-guide/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/getting-started/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/overview/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/tutorials/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/user-guide/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/user-guide/*/*.rst)
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

DOCKER_HUB_IMAGES_LATEST =\
    matejak/argbash:latest\
    minio/minio:latest\
    postgres:latest\
    redis:latest
CI_IMAGES_LATEST =
LAB_IMAGES_LATEST =

BEAUTIFY_SENTINEL = $(PROJECT_BUILD_DIR)/.beautify.sentinel
CODE_PACKAGING_SENTINEL = $(PROJECT_BUILD_DIR)/.code-packaging.sentinel
CODE_INTEGRATION_TESTS_SENTINEL = $(PROJECT_BUILD_DIR)/.integration-tests.sentinel
CODE_UNIT_TESTS_SENTINEL = $(PROJECT_BUILD_DIR)/.unit-tests.sentinel
CONDA_CREATE_SENTINEL = $(PROJECT_BUILD_DIR)/.conda-create.sentinel
CONDA_UPDATE_SENTINEL = $(PROJECT_BUILD_DIR)/.conda-update.sentinel
CONDA_ENV_DEV_INSTALL_SENTINEL = $(PROJECT_BUILD_DIR)/.conda-env-dev-install.sentinel
CONDA_ENV_PIP_INSTALL_SENTINEL = $(PROJECT_BUILD_DIR)/.conda-env-pip-install.sentinel
CONTAINER_CONDA_ENV_FILES =
CONTAINER_SCRIPTS =
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
$(RM) -f $(CODE_PACKAGING_SENTINEL)
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

define get_host_group_id
$(shell id -g)
endef

define package_code
$(call run_docker,\
    run\
    -t\
    --rm\
    -e PIP_CACHE_DIR=/work/.pip-cache\
    -u $(strip $(call get_host_user_id)):$(strip $(call get_host_group_id))\
    -v $(PROJECT_DIR):/work\
    $(CONTAINER_PYTHON_BUILD_IMAGE_LATEST)\
    /usr/local/bin/python -m build -sw)
endef

define pull_docker_hub_images
@$(foreach image,$(1),\
    echo "Pulling image $(image) from Docker Hub";\
    echo "======================================";\
    $(DOCKER) pull $(image) || exit 1;\
    echo "";)
endef

define pull_mitre_docker_images
@$(foreach image,$(1),\
    echo "Pulling image $(image) from the MITRE Artifactory";\
    echo "=================================================";\
    $(DOCKER) pull $(strip $(2))/$(image) || exit 1;\
    $(DOCKER) tag $(strip $(2))/$(image) $(image) || exit 1;\
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
    -u $(strip $(call get_host_user_id)):$(strip $(call get_host_group_id))\
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
MINICONDA_VERSION=$(CONTAINER_MINICONDA_VERSION)\
PYTORCH_VERSION=$(CONTAINER_PYTORCH_VERSION)\
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
$(PYTEST) --import-mode=importlib $(1)
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
    -u $(strip $(call get_host_user_id)):$(strip $(call get_host_group_id))\
    $(CONTAINER_SPHINX_IMAGE_LATEST)\
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
    -u $(strip $(call get_host_user_id)):$(strip $(call get_host_group_id))\
    -v $(PROJECT_DIR):/work\
    --entrypoint ""\
    --workdir /work\
    $(CONTAINER_TOX_PY37_IMAGE_LATEST)\
    $(TOX))
endef

define run_tox_py38
$(call run_docker,\
    run\
    -t\
    --rm\
    -e PIP_CACHE_DIR=/work/.tox/pip-cache-py38\
    -u $(strip $(call get_host_user_id)):$(strip $(call get_host_group_id))\
    -v $(PROJECT_DIR):/work\
    --entrypoint ""\
    --workdir /work\
    $(CONTAINER_TOX_PY38_IMAGE_LATEST)\
    $(TOX))
endef

define run_yq
$(call run_docker,\
    run\
    -t\
    --rm\
    -v $(PROJECT_DIR):/workdir\
    -u $(strip $(call get_host_user_id)):$(strip $(call get_host_group_id))\
    mikefarah/yq\
    $(strip $(1))\
    $(strip $(2)))
endef

define generate_gitlab_ci_version_vars
( $(call run_yq,\
    --no-colors\
    --prettyPrint\
    eval\
    --null-input\
    --unwrapScalar=false\
    '{"variables": {\
        "OS_VERSION": "$(CONTAINER_OS_VERSION)"$(COMMA)\
        "OS_VERSION_NUMBER": "$(CONTAINER_OS_VERSION_NUMBER)"$(COMMA)\
        "OS_BUILD_NUMBER": "$(CONTAINER_OS_BUILD_NUMBER)"$(COMMA)\
        "PROJECT_VERSION": "$(PROJECT_VERSION)"$(COMMA)\
        "MINICONDA_VERSION": "$(CONTAINER_MINICONDA_VERSION)"$(COMMA)\
        "PYTORCH_VERSION": "$(CONTAINER_PYTORCH_VERSION)"$(COMMA)\
        "SPHINX_VERSION": "$(CONTAINER_SPHINX_VERSION)"$(COMMA)\
        "TENSORFLOW2_VERSION": "$(CONTAINER_TENSORFLOW2_VERSION)"\
    }}',) ) >$(strip $(1))
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
	$(call run_build_script,$(3),$(4))
	$(call save_sentinel_file,$$@)
endef

define set_latest_tag_docker_image_recipe
$(strip $(1)): $(strip $(2)) | $$(PROJECT_BUILD_DIR)
	$(call docker_image_tag,$(3),$(4))
	$(call save_sentinel_file,$$@)
endef

define generate_docker_image_shellscripts_recipe
$(strip $(1)):

$(strip $(2))/%.sh: $$(PROJECT_DOCKER_SHELLSCRIPTS_DIR)/%.m4
	$(call run_argbash,\
		$$(PROJECT_DIR)/$$(PROJECT_DOCKER_SHELLSCRIPTS_DIR),\
		$$(PROJECT_DIR)/$(strip $(2)),\
		-o /output/$$(shell basename '$$@') /work/$$(shell basename '$$<'))
endef

define generate_docker_image_conda_env_recipe
$(strip $(1)):

$(strip $(2))/%.yml: $$(PROJECT_DOCKER_CONDA_ENV_DIR)/%.yml $$(VERSION_VARS_FILE)
	( $(call run_yq,\
		--no-colors\
		--prettyPrint\
		eval\
		'(.dependencies[] | select(. == "python")) = "python=$$(CONTAINER_PYTHON_VERSION)" | \
			(.dependencies[] | select(. == "scikit-learn")) = "scikit-learn=$$(CONTAINER_SKLEARN_VERSION)" | \
			(.dependencies[].pip[] | select(. == "adversarial-robustness-toolbox")) = "adversarial-robustness-toolbox==$$(CONTAINER_IBM_ART_VERSION)" | \
			(.dependencies[].pip[] | select(. == "mlflow")) = "mlflow==$$(CONTAINER_MLFLOW_VERSION)" | \
			(.dependencies[].pip[] | select(. == "prefect")) = "prefect==$$(CONTAINER_PREFECT_VERSION)"', \
		/workdir/$$<) ) >$$@
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
CONTAINER_CONDA_ENV_FILES += $$(CONTAINER_$(1)_CONDA_ENV_FILES)
CONTAINER_SCRIPTS += $$(CONTAINER_$(strip $(1))_SCRIPTS)
$(strip $(4))_IMAGES_LATEST += $$(CONTAINER_$(strip $(1))_IMAGE_LATEST)
endef

define generate_docker_image_pipeline
$(eval $(call build_docker_image_recipe,$(1),$(strip $(strip $(2) $(7)) $(10)),$(5),$(6)))
$(eval $(call set_latest_tag_docker_image_recipe,$(9),$(1),$(3),$(4)))
$(eval $(call generate_docker_image_shellscripts_recipe,$(7),$(8)))
$(eval $(call generate_docker_image_conda_env_recipe,$(10),$(8)))
endef

define generate_full_docker_image_vars
$(eval $(call define_docker_image_sentinel_vars,$(1),$(2),$(3),$(4)))
endef

define generate_full_docker_image_recipe
$(eval $(call generate_docker_image_pipeline,\
	$$(CONTAINER_$(1)_BUILD_SENTINEL),\
	$$($(2)) $$(CONTAINER_$(1)_DOCKERFILE) $$(CONTAINER_$(1)_INCLUDE_FILES),\
	$$(CONTAINER_$(1)_IMAGE),\
	$$(CONTAINER_$(1)_IMAGE_LATEST),\
	$$(CONTAINER_$(1)_COMPONENT_NAME),\
	$$($(3)),\
	$$(CONTAINER_$(1)_SCRIPTS),\
	$$(CONTAINER_$(1)_INCLUDE_DIR),\
	$$(CONTAINER_$(1)_BUILD_LATEST_SENTINEL),\
	$$(CONTAINER_$(1)_CONDA_ENV_FILES)))
endef

#################################################################################
# AUTO-GENERATED GLOBALS                                                        #
#################################################################################

$(call generate_full_docker_image_vars,SPHINX,CONTAINER_IMAGE_TAG,sphinx,CI)
$(call generate_full_docker_image_vars,MLFLOW_TRACKING,CONTAINER_IMAGE_TAG,mlflow-tracking,LAB)
$(call generate_full_docker_image_vars,NGINX,CONTAINER_IMAGE_TAG,nginx,LAB)
$(call generate_full_docker_image_vars,RESTAPI,CONTAINER_IMAGE_TAG,restapi,LAB)
$(call generate_full_docker_image_vars,PYTHON_BUILD,CONTAINER_IMAGE_TAG,python-build,CI)
$(call generate_full_docker_image_vars,PYTORCH_CPU,CONTAINER_IMAGE_TAG,pytorch-cpu,LAB)
$(call generate_full_docker_image_vars,PYTORCH_GPU,CONTAINER_IMAGE_TAG,pytorch-gpu,LAB)
$(call generate_full_docker_image_vars,TENSORFLOW2_CPU,CONTAINER_IMAGE_TAG,tensorflow2-cpu,LAB)
$(call generate_full_docker_image_vars,TENSORFLOW2_GPU,CONTAINER_IMAGE_TAG,tensorflow2-gpu,LAB)
$(call generate_full_docker_image_vars,TOX_PY37,CONTAINER_IMAGE_TAG,tox-py37,CI)
$(call generate_full_docker_image_vars,TOX_PY38,CONTAINER_IMAGE_TAG,tox-py38,CI)

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Reformat code
beautify: $(BEAUTIFY_SENTINEL)

## Build all Docker images in project
build-all: build-ci build-lab

## Build all continuous integration (CI) images
build-ci: build-python-build build-sphinx build-tox

## Build all Securing AI Lab images
build-lab: build-nginx build-mlflow-tracking build-restapi build-pytorch build-tensorflow

## Build the MLFlow Tracking Docker image
build-mlflow-tracking: $(CONTAINER_MLFLOW_TRACKING_BUILD_SENTINEL)

## Build the nginx Docker image
build-nginx: $(CONTAINER_NGINX_BUILD_SENTINEL)

## Build the Python Build Docker image
build-python-build: $(CONTAINER_PYTHON_BUILD_BUILD_SENTINEL)

## Build the PyTorch Docker images
build-pytorch: build-pytorch-cpu build-pytorch-gpu

## Build the PyTorch (CPU) Docker image
build-pytorch-cpu: $(CONTAINER_PYTORCH_CPU_BUILD_SENTINEL)

## Build the PyTorch (GPU) Docker image
build-pytorch-gpu: $(CONTAINER_PYTORCH_GPU_BUILD_SENTINEL)

## Build the restapi Docker image
build-restapi: $(CONTAINER_RESTAPI_BUILD_SENTINEL)

## Build the Sphinx image
build-sphinx: $(CONTAINER_SPHINX_BUILD_SENTINEL)

## Build the Tensorflow Docker images
build-tensorflow: build-tensorflow-cpu build-tensorflow-gpu

## Build the Tensorflow (CPU) Docker image
build-tensorflow-cpu: $(CONTAINER_TENSORFLOW2_CPU_BUILD_SENTINEL)

## Build the Tensorflow (GPU) Docker image
build-tensorflow-gpu: $(CONTAINER_TENSORFLOW2_GPU_BUILD_SENTINEL)

## Build the Tox Docker images
build-tox: $(CONTAINER_TOX_PY37_BUILD_SENTINEL) $(CONTAINER_TOX_PY38_BUILD_SENTINEL)

## Generate configuration files for GitLab CI
ci-deps: $(CI_VERSION_VARS_YML)

## Remove temporary files
clean: ; $(call cleanup)

## Lint and type check the source code
code-check: $(LINTING_SENTINEL) $(TYPE_CHECK_SENTINEL)

## Package source code for distribution
code-pkg: $(CODE_PACKAGING_SENTINEL)

## Update conda-based virtual environment
conda-env: $(CONDA_CREATE_SENTINEL) $(CONDA_UPDATE_SENTINEL) $(CONDA_ENV_PIP_INSTALL_SENTINEL) $(CONDA_ENV_DEV_INSTALL_SENTINEL)

## Generate configuration and script files for docker images
docker-deps: $(CONTAINER_CONDA_ENV_FILES) $(CONTAINER_SCRIPTS)

## Build project documentation
docs: $(DOCS_SENTINEL)

## Install pre-commit hooks
hooks: $(PRE_COMMIT_HOOKS_SENTINEL)

## Pull latest images from the MITRE artifactory and retag
pull-latest: pull-latest-hub pull-latest-ci pull-latest-lab

## Pull latest CI images from the MITRE artifactory and retag
pull-latest-ci: ; $(call pull_mitre_docker_images,$(CI_IMAGES_LATEST),$(ARTIFACTORY_UNTRUSTED_PREFIX))

## Pull latest vendor images from Docker Hub
pull-latest-hub: ; $(call pull_docker_hub_images,$(DOCKER_HUB_IMAGES_LATEST))

## Pull latest Lab images from the MITRE artifactory and retag
pull-latest-lab: ; $(call pull_mitre_docker_images,$(LAB_IMAGES_LATEST),$(ARTIFACTORY_UNTRUSTED_PREFIX))

## Manually set "latest" tag on all continuous integration (CI) images
tag-latest-ci: $(CONTAINER_PYTHON_BUILD_BUILD_LATEST_SENTINEL) $(CONTAINER_SPHINX_BUILD_LATEST_SENTINEL) $(CONTAINER_TOX_PY37_BUILD_LATEST_SENTINEL) $(CONTAINER_TOX_PY38_BUILD_LATEST_SENTINEL)

## Manually set "latest" tag on all Securing AI Lab images
tag-latest-lab: $(CONTAINER_NGINX_BUILD_LATEST_SENTINEL) $(CONTAINER_RESTAPI_BUILD_LATEST_SENTINEL) $(CONTAINER_MLFLOW_TRACKING_BUILD_LATEST_SENTINEL) $(CONTAINER_PYTORCH_CPU_BUILD_LATEST_SENTINEL) $(CONTAINER_PYTORCH_GPU_BUILD_LATEST_SENTINEL) $(CONTAINER_TENSORFLOW2_CPU_BUILD_LATEST_SENTINEL) $(CONTAINER_TENSORFLOW2_GPU_BUILD_LATEST_SENTINEL)

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

$(BEAUTIFY_SENTINEL): $(CODE_SRC_FILES) $(CODE_TASK_PLUGINS_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_python_black,$(PROJECT_SRC_SECURINGAI_DIR) $(PROJECT_TESTS_DIR) $(CODE_SECURINGAI_BUILTINS_DIR))
	$(call run_isort,$(PROJECT_SRC_SECURINGAI_DIR))
	$(call run_isort,$(CODE_SECURINGAI_BUILTINS_DIR))
	$(call run_isort,$(PROJECT_TESTS_DIR))
	$(call save_sentinel_file,$@)

$(CI_VERSION_VARS_YML): $(VERSION_VARS_FILE)
	$(call generate_gitlab_ci_version_vars,$@)

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

$(CODE_PACKAGING_SENTINEL): $(VERSION_VARS_FILE) $(CODE_PACKAGING_FILES) $(CODE_SRC_FILES) $(DOCS_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR) $(CODE_PIP_CACHE_DIR)
	$(call package_code,$(CODE_BUILD_DIR))
	$(call save_sentinel_file,$@)
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

$(CONDA_ENV_DEV_INSTALL_SENTINEL): | $(PROJECT_BUILD_DIR)
	$(call run_pip_install,-e .)
	$(call save_sentinel_file,$@)

$(DOCS_SENTINEL): $(DOCS_FILES) $(CODE_SRC_FILES) $(CODE_TASK_PLUGINS_FILES) | $(PROJECT_BUILD_DIR)
	@$(RM) -rf $(DOCS_BUILD_DIR)
	$(call run_sphinx_build,$(DOCS_SOURCE_DIR),$(DOCS_BUILD_DIR))
	@$(RM) -rf $(PROJECT_DOCS_DIR)/mlruns
	$(call save_sentinel_file,$@)

$(LINTING_SENTINEL): $(CODE_SRC_FILES) $(CODE_TASK_PLUGINS_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_flake8,$(PROJECT_SRC_SECURINGAI_DIR) $(CODE_SECURINGAI_BUILTINS_DIR) $(PROJECT_TESTS_DIR))
	$(call save_sentinel_file,$@)

$(PRE_COMMIT_HOOKS_SENTINEL): $(PRE_COMMIT_CONFIG_FILE) | $(PROJECT_BUILD_DIR)
	$(call pre_commit_cmd,install --install-hooks)
	$(call pre_commit_cmd,install --hook-type commit-msg)
	$(call save_sentinel_file,$@)

$(TYPE_CHECK_SENTINEL): $(CODE_SRC_FILES) $(CODE_TASK_PLUGINS_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_mypy,$(PROJECT_SRC_SECURINGAI_DIR) $(CODE_SECURINGAI_BUILTINS_DIR) $(PROJECT_TESTS_DIR))
	$(call save_sentinel_file,$@)

$(TOX_PY37_SENTINEL): $(TOX_CONFIG_FILE) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR) $(CODE_TOX_PY37_PIP_CACHE_DIR)
	$(call run_tox_py37)
	$(call save_sentinel_file,$@)

$(TOX_PY38_SENTINEL): $(TOX_CONFIG_FILE) $(CODE_UNIT_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR) $(CODE_TOX_PY38_PIP_CACHE_DIR)
	$(call run_tox_py38)
	$(call save_sentinel_file,$@)

#################################################################################
# AUTO-GENERATED PROJECT BUILD RECEIPES                                         #
#################################################################################

$(call generate_full_docker_image_recipe,SPHINX,,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,MLFLOW_TRACKING,,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,NGINX,,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,PYTHON_BUILD,,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,RESTAPI,CODE_PACKAGING_SENTINEL,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,PYTORCH_CPU,CODE_PACKAGING_SENTINEL,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,PYTORCH_GPU,CODE_PACKAGING_SENTINEL,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,TENSORFLOW2_CPU,CODE_PACKAGING_SENTINEL,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,TENSORFLOW2_GPU,CODE_PACKAGING_SENTINEL,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,TOX_PY37,,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,TOX_PY38,,CONTAINER_IMAGE_TAG)

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
