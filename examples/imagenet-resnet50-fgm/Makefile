.PHONY: clean data help
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

EXAMPLE_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
EXAMPLE_NAME = tensorflow-mnist-classifier
EXAMPLE_CONDA_ENV_NAME = securing-ai-lab-components
EXAMPLE_DATA_DIR = data
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

S3_WORKFLOW_BUCKET = workflow

MAKEFILE_FILE = Makefile
WORKFLOWS_TARBALL_FILE = workflows.tar.gz

DOCKER_INIT_SENTINEL = .docker-init.sentinel
DOCKER_COMPOSE_SENTINEL = .docker-compose.sentinel
WORKFLOWS_UPLOAD_SENTINEL = .workflows-upload.sentinel

#################################################################################
# FUNCTIONS                                                                     #
#################################################################################

define cleanup
	$(FIND) $(1) -name "__pycache__" -type d -exec $(RM) -rf {} +
	$(FIND) $(1) -name "*.py[co]" -type f -exec $(RM) -rf {} +
endef

define make_subdirectory
	mkdir -p "$(strip $(1))"
endef

#define set_permissions
#    chmod -R 777 "$(strip $(1))"
#endef

define make_tarball
	$(TAR) czf $(1) $(2)
endef

define run_docker
	$(DOCKER) $(1)
endef

define run_docker_compose
	$(DOCKER_COMPOSE) $(1)
endef

define s3_cp
	$(call run_docker_compose,\
		run\
		--rm\
		--entrypoint ""\
		-v $(strip $(1))/$(strip $(2)):/work/$(strip $(2))\
		tfcpu\
		s3-cp.sh --endpoint-url http://minio:9000\
		/work/$(strip $(2)) s3://$(strip $(3))/$(strip $(2)))
endef

define s3_mb
	$(call run_docker_compose,\
		run\
		--rm\
		--entrypoint ""\
		mlflow-tracking\
		s3-mb.sh --endpoint-url http://minio:9000 $(strip $(1)))
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
clean:
	$(call cleanup,$(EXAMPLE_DIR))

## Launch the Minio S3 and MLFlow Tracking services
services: $(DOCKER_COMPOSE_SENTINEL)

## Destroy service containers
teardown:
ifneq ("$(wildcard $(DOCKER_COMPOSE_SENTINEL))","")
	$(call run_docker_compose, down)
	$(RM) -f $(DOCKER_COMPOSE_SENTINEL)
endif

## Create job tarball and upload to Minio S3 storage
upload-job: services $(WORKFLOWS_UPLOAD_SENTINEL)

#################################################################################
# PROJECT SUPPORT RULES                                                         #
#################################################################################


$(DOCKER_COMPOSE_SENTINEL):
	$(call make_subdirectory,s3)
	$(call make_subdirectory,mlruns)
	$(call run_docker_compose,up -d mlflow-tracking)
	$(call s3_mb,$(S3_WORKFLOW_BUCKET))
	$(call save_sentinel_file,$@)

$(WORKFLOWS_TARBALL_FILE): $(CODE_SRC_FILES) $(CODE_WORKFLOW_FILE)
	$(call make_tarball,$@,$(CODE_SRC_FILES) $(CODE_WORKFLOW_FILE))

$(WORKFLOWS_UPLOAD_SENTINEL): $(WORKFLOWS_TARBALL_FILE)
	$(call s3_cp,$(EXAMPLE_DIR),$(WORKFLOWS_TARBALL_FILE),$(S3_WORKFLOW_BUCKET))
	$(call save_sentinel_file,$(WORKFLOWS_UPLOAD_SENTINEL))

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
