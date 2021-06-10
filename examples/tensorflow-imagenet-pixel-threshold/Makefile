# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
.PHONY: clean help jupyter teardown teardown-docker-compose teardown-docker-volumes teardown-docker-compose-sentinel workflows
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
CHOWN_PERM =
else ifeq ($(DETECTED_OS),Linux)
CORES = $(shell lscpu -p | egrep -v '^\#' | sort -u -t, -k 2,4 | wc -l)
CHOWN_PERM = 1
else
CORES = 1
CHOWN_PERM =
endif

EXAMPLE_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
EXAMPLE_NAME = tensorflow-imagenet-pixel-threshold
EXAMPLE_CONDA_ENV_NAME = imagenet-pixel-threshold
EXAMPLE_JUPYTER_DIR = jupyter
EXAMPLE_SRC_DIR = src

CONDA = conda
DOCKER = docker
DOCKER_COMPOSE = docker-compose
FIND = find
MV = mv
PY ?= python3.7
RM = rm
TAR = tar

CODE_SRC_FILES := $(wildcard $(EXAMPLE_SRC_DIR)/*.py)
CODE_WORKFLOW_FILE = MLproject

JUPYTER_INSTALL_PACKAGES_SCRIPT = $(EXAMPLE_JUPYTER_DIR)/before-notebook.d/install-packages.sh

MAKEFILE_FILE = Makefile
WORKFLOWS_TARBALL_FILE = workflows.tar.gz

DOCKER_VOLUME_PREFIX := $(shell basename $(EXAMPLE_DIR))
DOCKER_LOCAL_VOLUMES =\
    $(DOCKER_VOLUME_PREFIX)_before-notebook-scripts\
    $(DOCKER_VOLUME_PREFIX)_full-dir

JUPYTER_SENTINEL = .jupyter.sentinel

#################################################################################
# FUNCTIONS                                                                     #
#################################################################################

define chmod
chmod $(1) $(2)
endef

define chown
chown $(2) $(1)
endef

define cleanup
$(FIND) . \( -name "__pycache__" -and -not -path "./.tox*" \) -type d -exec $(RM) -rf {} +
$(FIND) . \( -name "*.py[co]" -and -not -path "./.tox*" \) -type f -exec $(RM) -rf {} +
$(FIND) . -name ".ipynb_checkpoints" -type d -exec $(RM) -rf {} +
$(RM) -rf $(EXAMPLE_DIR)/.mypy_cache
$(RM) -rf $(EXAMPLE_DIR)/$(WORKFLOWS_TARBALL_FILE)
endef

define get_host_user_id
$(shell id -u)
endef

define get_host_group_id
$(shell id -g)
endef

define make_subdirectory
mkdir -p "$(strip $(1))"
endef

define make_tarball
$(TAR) czf $(1) $(2)
endef

define run_docker
$(DOCKER) $(1)
endef

define run_docker_compose
$(DOCKER_COMPOSE) $(1)
endef

define docker_remove_volume
$(call run_docker,volume rm $(1))
endef

define save_sentinel_file
@touch $(1)
endef

define split_string_and_get_word
$(word $3,$(subst $2, ,$1))
endef

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Remove temporary files
clean: ; $(call cleanup)

## Launch the jupyter lab service
jupyter: $(JUPYTER_SENTINEL)

## Stop and remove the Testbed service containers
teardown: teardown-docker-compose teardown-docker-volumes teardown-docker-compose-sentinel

## Create workflows tarball
workflows: $(WORKFLOWS_TARBALL_FILE)

#################################################################################
# PROJECT SUPPORT RULES                                                         #
#################################################################################

$(JUPYTER_SENTINEL):
	$(call chmod,0755,$(JUPYTER_INSTALL_PACKAGES_SCRIPT))
	$(call run_docker_compose,up -d jupyter)
	$(call save_sentinel_file,$@)

$(WORKFLOWS_TARBALL_FILE): $(CODE_SRC_FILES) $(CODE_WORKFLOW_FILE)
	$(call make_tarball,$@,$(CODE_SRC_FILES) $(CODE_WORKFLOW_FILE))
	$(call chmod,644,$(WORKFLOWS_TARBALL_FILE))

teardown-docker-compose:
ifneq ("$(wildcard $(JUPYTER_SENTINEL))","")
	$(call run_docker_compose,down)
endif

teardown-docker-volumes:
ifneq ("$(wildcard $(JUPYTER_SENTINEL))","")
	$(call docker_remove_volume,$(DOCKER_LOCAL_VOLUMES))
endif

teardown-docker-compose-sentinel:
ifneq ("$(wildcard $(JUPYTER_SENTINEL))","")
	$(RM) -f $(JUPYTER_SENTINEL)
endif

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
