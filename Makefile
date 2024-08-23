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
.PHONY: beautify build-all build-mlflow-tracking build-nginx build-pytorch build-pytorch-cpu build-pytorch-gpu build-restapi build-tensorflow build-tensorflow-cpu build-tensorflow-gpu clean code-check code-pkg commit-check docs docs-check help tag-latest tests tests-containers tests-integration tests-unit tox venv
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

ifeq ($(OS),Windows_NT)
DETECTED_OS := Windows
else
DETECTED_OS := $(shell sh -c "uname 2>/dev/null || echo Unknown")
endif

PY ?= python
PYTHON_VERSION := $(word 2,$(strip $(shell /usr/bin/env $(PY) --version)))
PYTHON_VERSION_MAJOR := $(word 1,$(subst ., ,$(PYTHON_VERSION)))
PYTHON_VERSION_MINOR := $(word 2,$(subst ., ,$(PYTHON_VERSION)))

ARCH := $(strip $(shell /usr/bin/env $(PY) -c 'import platform; print(platform.machine().lower())'))

ifeq ($(ARCH),x86_64)
DETECTED_ARCH := amd64
else ifeq ($(ARCH),amd64)
DETECTED_ARCH := amd64
else ifeq ($(ARCH),aarch64)
DETECTED_ARCH := arm64
else ifeq ($(ARCH),arm64)
DETECTED_ARCH := arm64
endif

VENV_EXTRA ?=

ifeq ($(DETECTED_OS),Darwin)
CORES = $(shell sysctl -n hw.physicalcpu_max)
PIPTOOLS_SYNC := CFLAGS="-stdlib=libc++ -std=c99" pip-sync
VENV_REQUIREMENTS = requirements/macos-$(DETECTED_ARCH)-py$(PYTHON_VERSION_MAJOR).$(PYTHON_VERSION_MINOR)-requirements-dev$(VENV_EXTRA).txt
else ifeq ($(DETECTED_OS),Linux)
CORES = $(shell lscpu -p | egrep -v '^\#' | sort -u -t, -k 2,4 | wc -l)
PIPTOOLS_SYNC := pip-sync
VENV_REQUIREMENTS = requirements/linux-$(DETECTED_ARCH)-py$(PYTHON_VERSION_MAJOR).$(PYTHON_VERSION_MINOR)-requirements-dev$(VENV_EXTRA).txt
else
CORES = 1
PIPTOOLS_SYNC := pip-sync
VENV_REQUIREMENTS = requirements/win-$(DETECTED_ARCH)-py$(PYTHON_VERSION_MAJOR).$(PYTHON_VERSION_MINOR)-requirements-dev$(VENV_EXTRA).txt
endif

COMMA := ,
NO_CACHE ?=
VENV := .venv
PIPTOOLS_SYNC_COMMAND_AVAILABLE := $(shell command -v $(VENV)/bin/pip-sync 2> /dev/null)

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = dioptra
PROJECT_PREFIX = dioptra
PROJECT_BUILD_DIR = build
PROJECT_DOCS_DIR = docs
PROJECT_DOCKER_DIR = docker
PROJECT_DOCKER_SRC_DIR = $(PROJECT_DOCKER_DIR)/src
PROJECT_DOCKER_CONDA_ENV_DIR = $(PROJECT_DOCKER_SRC_DIR)/conda-env
PROJECT_DOCKER_SHELLSCRIPTS_DIR = $(PROJECT_DOCKER_SRC_DIR)/shellscripts
PROJECT_SRC_DIR = src
PROJECT_SRC_DIOPTRA_DIR = $(PROJECT_SRC_DIR)/dioptra
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
RM = rm
SPHINX_BUILD = sphinx-build
TOX = tox

CONTAINER_VARS_FILE = container-vars.mk
MAKEFILE_FILE = Makefile
TOX_CONFIG_FILE = tox.ini
VERSION_VARS_FILE = version-vars.mk

CODE_PKG_NAME = dioptra
CODE_BUILD_DIR = dist
CODE_COOKIECUTTER_TESTS_DIR = $(PROJECT_TESTS_DIR)/cookiecutter_dioptra_deployment
CODE_CONTAINER_TESTS_DIR = $(PROJECT_TESTS_DIR)/containers
CODE_INTEGRATION_TESTS_DIR = $(PROJECT_TESTS_DIR)/integration
CODE_DIOPTRA_BUILTINS_DIR = $(PROJECT_TASK_PLUGINS_DIR)/dioptra_builtins
CODE_UNIT_TESTS_DIR = $(PROJECT_TESTS_DIR)/unit
CODE_SRC_FILES := $(wildcard $(PROJECT_SRC_DIOPTRA_DIR)/generics_plugins/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIOPTRA_DIR)/generics_plugins/*/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIOPTRA_DIR)/mlflow_plugins/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIOPTRA_DIR)/pyplugs/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIOPTRA_DIR)/restapi/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIOPTRA_DIR)/restapi/*/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIOPTRA_DIR)/restapi/*/*/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIOPTRA_DIR)/rq/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIOPTRA_DIR)/rq/*/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIOPTRA_DIR)/sdk/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIOPTRA_DIR)/sdk/*/*.py)
CODE_SRC_FILES += $(wildcard $(PROJECT_SRC_DIOPTRA_DIR)/sdk/*/*/*.py)
CODE_COOKIECUTTER_TESTS_FILES := $(wildcard $(CODE_COOKIECUTTER_TESTS_DIR)/*.py)
CODE_COOKIECUTTER_TESTS_FILES += $(wildcard $(CODE_COOKIECUTTER_TESTS_DIR)/*/*.py)
CODE_COOKIECUTTER_TESTS_FILES += $(wildcard $(CODE_COOKIECUTTER_TESTS_DIR)/*/*/*.py)
CODE_COOKIECUTTER_TESTS_FILES += $(wildcard $(CODE_COOKIECUTTER_TESTS_DIR)/*/*/*/*.py)
CODE_CONTAINER_TESTS_FILES := $(wildcard $(CODE_CONTAINER_TESTS_DIR)/*.py)
CODE_CONTAINER_TESTS_FILES += $(wildcard $(CODE_CONTAINER_TESTS_DIR)/*/*.py)
CODE_CONTAINER_TESTS_FILES += $(wildcard $(CODE_CONTAINER_TESTS_DIR)/*/*/*.py)
CODE_CONTAINER_TESTS_FILES += $(wildcard $(CODE_CONTAINER_TESTS_DIR)/*/*/*/*.py)
CODE_INTEGRATION_TESTS_FILES := $(wildcard $(CODE_INTEGRATION_TESTS_DIR)/*.py)
CODE_INTEGRATION_TESTS_FILES += $(wildcard $(CODE_INTEGRATION_TESTS_DIR)/*/*.py)
CODE_INTEGRATION_TESTS_FILES += $(wildcard $(CODE_INTEGRATION_TESTS_DIR)/*/*/*.py)
CODE_INTEGRATION_TESTS_FILES += $(wildcard $(CODE_INTEGRATION_TESTS_DIR)/*/*/*/*.py)
CODE_UNIT_TESTS_FILES := $(wildcard $(CODE_UNIT_TESTS_DIR)/*.py)
CODE_UNIT_TESTS_FILES += $(wildcard $(CODE_UNIT_TESTS_DIR)/*/*.py)
CODE_UNIT_TESTS_FILES += $(wildcard $(CODE_UNIT_TESTS_DIR)/*/*/*.py)
CODE_UNIT_TESTS_FILES += $(wildcard $(CODE_UNIT_TESTS_DIR)/*/*/*/*.py)
CODE_TASK_PLUGINS_FILES := $(wildcard $(CODE_DIOPTRA_BUILTINS_DIR)/*.py)
CODE_TASK_PLUGINS_FILES += $(wildcard $(CODE_DIOPTRA_BUILTINS_DIR)/*/*.py)
CODE_TASK_PLUGINS_FILES += $(wildcard $(CODE_DIOPTRA_BUILTINS_DIR)/*/*/*.py)
CODE_TASK_PLUGINS_FILES += $(wildcard $(CODE_DIOPTRA_BUILTINS_DIR)/*/*/*/*.py)
CODE_PACKAGING_FILES =\
    $(DOCS_FILES)\
    $(TOX_CONFIG_FILE)\
    MANIFEST.in\
    pyproject.toml
CODE_DISTRIBUTION_FILES =\
    $(CODE_BUILD_DIR)/$(CODE_PKG_NAME)-$(CODE_PKG_VERSION).tar.gz\
    $(CODE_BUILD_DIR)/$(subst -,_,$(CODE_PKG_NAME))-$(CODE_PKG_VERSION)-py3-none-any.whl

DOCS_ASSETS_DIR = $(PROJECT_DOCS_DIR)/assets
DOCS_BUILD_DIR = $(PROJECT_DOCS_DIR)/build
DOCS_SOURCE_DIR = $(PROJECT_DOCS_DIR)/source
DOCS_SCSS_DIR = $(DOCS_ASSETS_DIR)/scss
DOCS_FILES := $(wildcard $(DOCS_SOURCE_DIR)/*.py)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/deployment-guide/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/deployment-guide/*/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/dev-guide/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/getting-started/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/overview/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/tutorials/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/tutorials/*/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/user-guide/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/user-guide/*/*.rst)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/_static/*)
DOCS_FILES += $(wildcard $(DOCS_SOURCE_DIR)/_templates/*)
DOCS_WEB_COMPILE_FILES := $(wildcard $(DOCS_SCSS_DIR)/*.scss)

PIP :=
ifeq ($(DETECTED_OS),Darwin)
PIP += CFLAGS="-stdlib=libc++ -std=c99" $(PY) -m pip
else
PIP += $(PY) -m pip
endif

USE_BUILDKIT ?= true
BUILD_TARGET ?= final
DOCKER_BUILDKIT_VALUE = $(if $(USE_BUILDKIT),1,)
DOCKER_BUILD_TARGET = $(BUILD_TARGET)
DOCKER_NO_CACHE = $(if $(NO_CACHE),--no-cache,)
CONTAINER_IMAGE_TAG = dev

BEAUTIFY_SENTINEL = $(PROJECT_BUILD_DIR)/.beautify.sentinel
CODE_PACKAGING_SENTINEL = $(PROJECT_BUILD_DIR)/.code-packaging.sentinel
CODE_CONTAINER_TESTS_SENTINEL = $(PROJECT_BUILD_DIR)/.container-tests.sentinel
CODE_INTEGRATION_TESTS_SENTINEL = $(PROJECT_BUILD_DIR)/.integration-tests.sentinel
CODE_UNIT_TESTS_SENTINEL = $(PROJECT_BUILD_DIR)/.unit-tests.sentinel
DOCS_SENTINEL = $(PROJECT_BUILD_DIR)/.docs.sentinel
DOCS_LINTING_SENTINEL = $(PROJECT_BUILD_DIR)/.docs-linting.sentinel
GITLINT_SENTINEL = $(PROJECT_BUILD_DIR)/.gitlint.sentinel
LINTING_SENTINEL = $(PROJECT_BUILD_DIR)/.linting.sentinel
TOX_SENTINEL = $(PROJECT_BUILD_DIR)/.tox.sentinel
TYPE_CHECK_SENTINEL = $(PROJECT_BUILD_DIR)/.type-check.sentinel
VENV_SENTINEL = $(PROJECT_BUILD_DIR)/.venv.sentinel

#################################################################################
# FUNCTIONS                                                                     #
#################################################################################

define cleanup
$(FIND) . \( -name "__pycache__" -and -not -path "./.tox*" \) -type d -exec $(RM) -rf {} +
$(FIND) . \( -name "*.py[co]" -and -not -path "./.tox*" \) -type f -exec $(RM) -rf {} +
$(FIND) . -name ".ipynb_checkpoints" -type d -exec $(RM) -rf {} +
$(RM) -rf .coverage
$(RM) -rf coverage
$(RM) -rf dist
$(RM) -rf htmlcov
$(RM) -rf mlruns
$(RM) -rf $(PROJECT_BUILD_DIR)/bdist*
$(RM) -rf $(PROJECT_BUILD_DIR)/docs
$(RM) -rf $(PROJECT_BUILD_DIR)/lib
$(RM) -f $(PROJECT_BUILD_DIR)/.docker-image-*.sentinel
$(RM) -f $(BEAUTIFY_SENTINEL)
$(RM) -f $(CODE_PACKAGING_SENTINEL)
$(RM) -f $(CODE_CONTAINER_TESTS_SENTINEL)
$(RM) -f $(CODE_INTEGRATION_TESTS_SENTINEL)
$(RM) -f $(CODE_UNIT_TESTS_SENTINEL)
$(RM) -f $(DOCS_SENTINEL)
$(RM) -f $(DOCS_LINTING_SENTINEL)
$(RM) -f $(GITLINT_SENTINEL)
$(RM) -f $(LINTING_SENTINEL)
$(RM) -f $(TOX_SENTINEL)
$(RM) -f $(TYPE_CHECK_SENTINEL)
$(RM) -f $(VENV_SENTINEL)
$(RM) -rf $(PROJECT_DOCS_DIR)/build
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
$(call run_in_venv,$(VENV),$(PY) -m build,)
endef

define run_black
$(call run_in_venv,$(VENV),$(PY) -m $(TOX) -e black $(1),)
endef

define run_doc8
$(call run_in_venv,$(VENV),$(PY) -m $(TOX) -e doc8,)
endef

define run_flake8
$(call run_in_venv,$(VENV),$(PY) -m $(TOX) -e flake8,)
endef

define run_gitlint
$(call run_in_venv,$(VENV),$(PY) -m $(TOX) -e gitlint,)
endef

define run_isort
$(call run_in_venv,$(VENV),$(PY) -m $(TOX) -e isort $(1),)
endef

define run_mypy
$(call run_in_venv,$(VENV),$(PY) -m $(TOX) -e mypy,)
endef

define run_pip_install
$(call run_in_venv,$(VENV),$(PIP) install $(1),)
endef

define run_piptools_sync
$(call run_in_venv,$(VENV),$(PIPTOOLS_SYNC) $(1),)
endef

define run_pytest
$(call run_in_venv,$(VENV),$(PY) -m $(TOX) -e py$(PYTHON_VERSION_MAJOR)$(PYTHON_VERSION_MINOR)-pytest,)
endef

define run_rstcheck
$(call run_in_venv,$(VENV),$(PY) -m $(TOX) -e rstcheck,)
endef

define run_sphinx_build
$(call run_in_venv,$(VENV),$(PY) -m $(TOX) -e "web-compile$(COMMA)docs",)
endef

define run_tox
$(call run_in_venv,$(VENV),$(PY) -m $(TOX) run -e $(1),)
endef

define run_tox_all
$(call run_in_venv,$(VENV),$(PY) -m $(TOX) run-parallel --parallel $(CORES),)
endef

define run_venv
$(PY) -m venv $(strip $(1))
endef

define run_in_venv
bash -lc "source $(1)/bin/activate &&\
$(2) &&\
deactivate"
endef

define run_build_script
IMAGE_TAG=$(strip $(2))\
PROJECT_PREFIX=$(PROJECT_PREFIX)\
PROJECT_COMPONENT=$(strip $(1))\
DOCKER_BUILDKIT_VALUE=$(DOCKER_BUILDKIT_VALUE)\
DOCKER_BUILD_TARGET=$(DOCKER_BUILD_TARGET)\
DOCKER_NO_CACHE=$(DOCKER_NO_CACHE)\
docker/build.sh
endef

define run_docker
$(DOCKER) $(1)
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

define define_docker_image_sentinel_vars
CONTAINER_$(strip $(1))_COMPONENT_NAME = $(strip $(3))
CONTAINER_$(strip $(1))_IMAGE = $$(PROJECT_PREFIX)/$$(CONTAINER_$(strip $(1))_COMPONENT_NAME):$$($(strip $(2)))
CONTAINER_$(strip $(1))_IMAGE_LATEST = $$(PROJECT_PREFIX)/$$(CONTAINER_$(strip $(1))_COMPONENT_NAME):latest
CONTAINER_$(strip $(1))_DOCKERFILE = $$(PROJECT_DOCKER_DIR)/Dockerfile.$(strip $(3))
CONTAINER_$(strip $(1))_BUILD_SENTINEL = $$(PROJECT_BUILD_DIR)/.docker-image-$$(CONTAINER_$(strip $(1))_COMPONENT_NAME)-tag-$$($(strip $(2))).sentinel
CONTAINER_$(strip $(1))_BUILD_LATEST_SENTINEL = $$(PROJECT_BUILD_DIR)/.docker-image-$$(CONTAINER_$(strip $(1))_COMPONENT_NAME)-tag-latest.sentinel
endef

define generate_docker_image_pipeline
$(eval $(call build_docker_image_recipe,$(1),$(strip $(2)),$(5),$(6)))
$(eval $(call set_latest_tag_docker_image_recipe,$(7),$(1),$(3),$(4)))
endef

define generate_full_docker_image_vars
$(eval $(call define_docker_image_sentinel_vars,$(1),$(2),$(3)))
endef

define generate_full_docker_image_recipe
$(eval $(call generate_docker_image_pipeline,\
	$$(CONTAINER_$(1)_BUILD_SENTINEL),\
	$$(CONTAINER_$(1)_DOCKERFILE) $$(CONTAINER_$(1)_INCLUDE_FILES),\
	$$(CONTAINER_$(1)_IMAGE),\
	$$(CONTAINER_$(1)_IMAGE_LATEST),\
	$$(CONTAINER_$(1)_COMPONENT_NAME),\
	$$($(2)),\
	$$(CONTAINER_$(1)_BUILD_LATEST_SENTINEL)))
endef

#################################################################################
# AUTO-GENERATED GLOBALS                                                        #
#################################################################################

$(call generate_full_docker_image_vars,MLFLOW_TRACKING,CONTAINER_IMAGE_TAG,mlflow-tracking)
$(call generate_full_docker_image_vars,NGINX,CONTAINER_IMAGE_TAG,nginx)
$(call generate_full_docker_image_vars,RESTAPI,CONTAINER_IMAGE_TAG,restapi)
$(call generate_full_docker_image_vars,PYTORCH_CPU,CONTAINER_IMAGE_TAG,pytorch-cpu)
$(call generate_full_docker_image_vars,PYTORCH_GPU,CONTAINER_IMAGE_TAG,pytorch-gpu)
$(call generate_full_docker_image_vars,TENSORFLOW2_CPU,CONTAINER_IMAGE_TAG,tensorflow2-cpu)
$(call generate_full_docker_image_vars,TENSORFLOW2_GPU,CONTAINER_IMAGE_TAG,tensorflow2-gpu)

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Reformat code
beautify: $(BEAUTIFY_SENTINEL)

## Build all Dioptra images
build-all: build-nginx build-mlflow-tracking build-restapi build-pytorch build-tensorflow

## Build the MLFlow Tracking Docker image
build-mlflow-tracking: $(CONTAINER_MLFLOW_TRACKING_BUILD_SENTINEL)

## Build the nginx Docker image
build-nginx: $(CONTAINER_NGINX_BUILD_SENTINEL)

## Build the PyTorch Docker images
build-pytorch: build-pytorch-cpu build-pytorch-gpu

## Build the PyTorch (CPU) Docker image
build-pytorch-cpu: $(CONTAINER_PYTORCH_CPU_BUILD_SENTINEL)

## Build the PyTorch (GPU) Docker image
build-pytorch-gpu: $(CONTAINER_PYTORCH_GPU_BUILD_SENTINEL)

## Build the restapi Docker image
build-restapi: $(CONTAINER_RESTAPI_BUILD_SENTINEL)

## Build the Tensorflow Docker images
build-tensorflow: build-tensorflow-cpu build-tensorflow-gpu

## Build the Tensorflow (CPU) Docker image
build-tensorflow-cpu: $(CONTAINER_TENSORFLOW2_CPU_BUILD_SENTINEL)

## Build the Tensorflow (GPU) Docker image
build-tensorflow-gpu: $(CONTAINER_TENSORFLOW2_GPU_BUILD_SENTINEL)

## Remove temporary files
clean: ; $(call cleanup)

## Lint and type check the source code
code-check: $(LINTING_SENTINEL) $(TYPE_CHECK_SENTINEL) $(GITLINT_SENTINEL)

## Package source code for distribution
code-pkg: $(CODE_PACKAGING_SENTINEL)

## Lint the most recent commit message
commit-check: $(GITLINT_SENTINEL)

## Build project documentation
docs: $(DOCS_SENTINEL)

## Lint the docs
docs-check: $(DOCS_LINTING_SENTINEL)

## Manually set "latest" tag on all Dioptra images
tag-latest: $(CONTAINER_NGINX_BUILD_LATEST_SENTINEL) $(CONTAINER_RESTAPI_BUILD_LATEST_SENTINEL) $(CONTAINER_MLFLOW_TRACKING_BUILD_LATEST_SENTINEL) $(CONTAINER_PYTORCH_CPU_BUILD_LATEST_SENTINEL) $(CONTAINER_PYTORCH_GPU_BUILD_LATEST_SENTINEL) $(CONTAINER_TENSORFLOW2_CPU_BUILD_LATEST_SENTINEL) $(CONTAINER_TENSORFLOW2_GPU_BUILD_LATEST_SENTINEL)

## Run all tests
tests: tests-unit tests-containers tests-integration

## Run container tests
tests-containers: $(CODE_CONTAINER_TESTS_SENTINEL)

## Run integration tests
tests-integration: $(CODE_INTEGRATION_TESTS_SENTINEL)

## Run unit tests
tests-unit: $(CODE_UNIT_TESTS_SENTINEL)

## Run all basic tox tests
tox: $(TOX_SENTINEL)

## Install and update the project virtual environment
venv: $(VENV_SENTINEL)

#################################################################################
# PROJECT BUILD RECIPES                                                         #
#################################################################################

$(PROJECT_BUILD_DIR): ; $(call make_subdirectory,$@)
$(VENV): ; $(call run_venv,$@)

$(BEAUTIFY_SENTINEL): $(CODE_SRC_FILES) $(CODE_TASK_PLUGINS_FILES) $(CODE_UNIT_TESTS_FILES) $(CODE_CONTAINER_TESTS_FILES) $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_black,-- $(PROJECT_SRC_DIOPTRA_DIR) $(CODE_DIOPTRA_BUILTINS_DIR) $(PROJECT_TESTS_DIR))
	$(call run_isort,-- $(PROJECT_SRC_DIOPTRA_DIR) $(CODE_DIOPTRA_BUILTINS_DIR) $(PROJECT_TESTS_DIR))
	$(call save_sentinel_file,$@)

$(CODE_CONTAINER_TESTS_SENTINEL): $(CODE_CONTAINER_TESTS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_tox,py$(PYTHON_VERSION_MAJOR)$(PYTHON_VERSION_MINOR)-pytest -- $(CODE_CONTAINER_TESTS_DIR))
	$(call save_sentinel_file,$@)

$(CODE_INTEGRATION_TESTS_SENTINEL): $(CODE_INTEGRATION_TESTS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_tox,py$(PYTHON_VERSION_MAJOR)$(PYTHON_VERSION_MINOR)-pytest -- $(CODE_INTEGRATION_TESTS_DIR))
	$(call save_sentinel_file,$@)

$(CODE_UNIT_TESTS_SENTINEL): $(CODE_UNIT_TESTS_FILES) $(CODE_COOKIECUTTER_TESTS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_tox,py$(PYTHON_VERSION_MAJOR)$(PYTHON_VERSION_MINOR)-pytest -- $(CODE_UNIT_TESTS_DIR))
	$(call run_tox,py$(PYTHON_VERSION_MAJOR)$(PYTHON_VERSION_MINOR)-cookiecutter)
	$(call save_sentinel_file,$@)

$(CODE_PACKAGING_SENTINEL): $(VERSION_VARS_FILE) $(CODE_PACKAGING_FILES) $(CODE_SRC_FILES) $(DOCS_FILES) | $(PROJECT_BUILD_DIR)
	$(call package_code)
	$(call save_sentinel_file,$@)
	@echo ""
	@echo "$(CODE_PKG_NAME) packaged for distribution in $(CODE_BUILD_DIR)"

$(DOCS_SENTINEL): $(DOCS_WEB_COMPILE_FILES) $(DOCS_FILES) $(CODE_SRC_FILES) $(CODE_TASK_PLUGINS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_sphinx_build)
	@$(RM) -rf $(PROJECT_DOCS_DIR)/mlruns
	$(call save_sentinel_file,$@)

$(DOCS_LINTING_SENTINEL): $(DOCS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_doc8)
	$(call run_rstcheck)
	$(call save_sentinel_file,$@)

$(GITLINT_SENTINEL): | $(PROJECT_BUILD_DIR)
	$(call run_gitlint)
	$(call save_sentinel_file,$@)

$(LINTING_SENTINEL): $(CODE_SRC_FILES) $(CODE_TASK_PLUGINS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_flake8)
	$(call save_sentinel_file,$@)

$(TYPE_CHECK_SENTINEL): $(CODE_SRC_FILES) $(CODE_TASK_PLUGINS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_mypy)
	$(call save_sentinel_file,$@)

$(TOX_SENTINEL): $(TOX_CONFIG_FILE) $(CODE_SRC_FILES) $(CODE_TASK_PLUGINS_FILES) $(CODE_UNIT_TESTS_FILES) | $(PROJECT_BUILD_DIR)
	$(call run_tox_all)
	$(call save_sentinel_file,$@)

$(VENV_SENTINEL): $(VENV_REQUIREMENTS) | $(PROJECT_BUILD_DIR) $(VENV)
ifndef PIPTOOLS_SYNC_COMMAND_AVAILABLE
	$(call run_pip_install,--upgrade pip setuptools pip-tools)
endif
	$(call run_piptools_sync,$(VENV_REQUIREMENTS))
	$(call save_sentinel_file,$@)

#################################################################################
# AUTO-GENERATED PROJECT BUILD RECIPES                                          #
#################################################################################

$(call generate_full_docker_image_recipe,MLFLOW_TRACKING,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,NGINX,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,RESTAPI,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,PYTORCH_CPU,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,PYTORCH_GPU,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,TENSORFLOW2_CPU,CONTAINER_IMAGE_TAG)
$(call generate_full_docker_image_recipe,TENSORFLOW2_GPU,CONTAINER_IMAGE_TAG)

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
