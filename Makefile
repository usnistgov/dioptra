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
.PHONY: build-all build-mlflow-tracking build-nginx build-pytorch build-pytorch-cpu build-pytorch-gpu build-restapi build-tensorflow build-tensorflow-cpu build-tensorflow-gpu clean help tag-latest
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

PY ?= python
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

NO_CACHE ?=

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = dioptra
PROJECT_PREFIX = dioptra
PROJECT_BUILD_DIR = build
PROJECT_DOCS_DIR = docs
PROJECT_DOCKER_DIR = docker

DOCKER = docker
FIND = find
RM = rm

BUILD_TARGET ?= final
DOCKER_BUILD_TARGET = $(BUILD_TARGET)
DOCKER_NO_CACHE = $(if $(NO_CACHE),--no-cache,)
CONTAINER_IMAGE_TAG = dev

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
$(RM) -f $(PROJECT_BUILD_DIR)/.docker-image-*.sentinel
$(RM) -rf $(PROJECT_DOCS_DIR)/build
endef

define docker_image_tag
$(call run_docker,tag $(strip $(1)) $(strip $(2)))
endef

define make_subdirectory
mkdir -p "$(strip $(1))"
endef

define run_build_script
./build-container.sh --image-tag "$(strip $(2))" --image-prefix "$(PROJECT_PREFIX)" --dockerfile-suffix "$(strip $(1))" --build-target "$(DOCKER_BUILD_TARGET)" --targetarch "$(DETECTED_ARCH)" $(DOCKER_NO_CACHE)
endef

define run_docker
$(DOCKER) $(1)
endef

define build_docker_image_recipe
$(strip $(1)): $(strip $(2)) | $$(PROJECT_BUILD_DIR)
	$(call run_build_script,$(3),$(4))
endef

define set_latest_tag_docker_image_recipe
$(strip $(1)): $(strip $(2)) | $$(PROJECT_BUILD_DIR)
	$(call docker_image_tag,$(3),$(4))
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
	$$(CONTAINER_$(1)_DOCKERFILE),\
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

## Manually set "latest" tag on all Dioptra images
tag-latest: $(CONTAINER_NGINX_BUILD_LATEST_SENTINEL) $(CONTAINER_RESTAPI_BUILD_LATEST_SENTINEL) $(CONTAINER_MLFLOW_TRACKING_BUILD_LATEST_SENTINEL) $(CONTAINER_PYTORCH_CPU_BUILD_LATEST_SENTINEL) $(CONTAINER_PYTORCH_GPU_BUILD_LATEST_SENTINEL) $(CONTAINER_TENSORFLOW2_CPU_BUILD_LATEST_SENTINEL) $(CONTAINER_TENSORFLOW2_GPU_BUILD_LATEST_SENTINEL)

#################################################################################
# PROJECT BUILD RECIPES                                                         #
#################################################################################

$(PROJECT_BUILD_DIR): ; $(call make_subdirectory,$@)

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
