.PHONY: clean data demo help initdb jupyter plugins services teardown teardown-docker-compose teardown-docker-volumes teardown-docker-compose-sentinel workflows
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
EXAMPLE_NAME = tensorflow-mnist-feature-squeezing
EXAMPLE_CONDA_ENV_NAME = feature_squeeze_mnist
EXAMPLE_DATA_DIR = data
EXAMPLE_JUPYTER_DIR = jupyter
EXAMPLE_MINIO_DATA_DIR = s3
EXAMPLE_MLFLOW_TRACKING_DATA_DIR = mlruns
EXAMPLE_PLUGINS_DIR = $(realpath ../../task-plugins)
EXAMPLE_REDIS_DATA_DIR = redis
EXAMPLE_RESTAPI_DATA_DIR = restapi
EXAMPLE_SRC_DIR = src

CONDA = conda
DOCKER = docker
DOCKER_COMPOSE = docker-compose
FIND = find
MV = mv
PY ?= python3.7
RM = rm
TAR = tar

CONDA_ENV_NAME = mitre-securing-ai

CODE_SRC_FILES := $(wildcard $(EXAMPLE_SRC_DIR)/*.py)
CODE_WORKFLOW_FILE = MLproject

PLUGINS_BUILTINS_DIR := $(EXAMPLE_PLUGINS_DIR)/securingai_builtins
PLUGINS_SRC_FILES := $(wildcard $(PLUGINS_BUILTINS_DIR)/*/*.py)

JUPYTER_INSTALL_PACKAGES_SCRIPT = $(EXAMPLE_JUPYTER_DIR)/before-notebook.d/install-packages.sh

RESTAPI_DATABASE = $(EXAMPLE_RESTAPI_DIR)/securingai.db
RESTAPI_DATABASE_INIT_SCRIPT_FILE = initdb.py

S3_PLUGINS_BUCKET = plugins
S3_WORKFLOW_BUCKET = workflow

MAKEFILE_FILE = Makefile
DATA_DOWNLOAD_FILE = $(EXAMPLE_DATA_DIR)/download_data.py
WORKFLOWS_TARBALL_FILE = workflows.tar.gz

DOCKER_VOLUME_PREFIX := $(shell basename $(EXAMPLE_DIR))
DOCKER_LOCAL_VOLUMES =\
    $(DOCKER_VOLUME_PREFIX)_before-notebook-scripts\
    $(DOCKER_VOLUME_PREFIX)_full-dir\
    $(DOCKER_VOLUME_PREFIX)_minio-data\
    $(DOCKER_VOLUME_PREFIX)_mlflow-tracking-data\
    $(DOCKER_VOLUME_PREFIX)_nfs-datasets\
    $(DOCKER_VOLUME_PREFIX)_redis-data\
    $(DOCKER_VOLUME_PREFIX)_restapi-data

DOCKER_COMPOSE_SENTINEL = .docker-compose.sentinel
JUPYTER_SENTINEL = .jupyter.sentinel
PLUGINS_SENTINEL = .plugins.sentinel
TRAINING_DATASET_SENTINEL = .training-dataset.sentinel
TESTING_DATASET_SENTINEL = .testing-dataset.sentinel

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

define download_data
$(call run_docker_compose,\
    run\
    --rm\
    --entrypoint ""\
    -v $(strip $(1)):/work/demo\
    -u $(strip $(call get_host_user_id)):$(strip $(call get_host_group_id))\
    -w /work/demo\
    tfcpu-01\
    bash -c "\
        source /opt/conda/etc/profile.d/conda.sh &&\
        conda activate $(CONDA_ENV_NAME) &&\
        $(PY) $(DATA_DOWNLOAD_FILE) --data-dir $(2) $(3)")
endef

define get_host_user_id
$(shell id -u)
endef

define get_host_group_id
$(shell id -g)
endef

define init_database
$(call run_docker_compose,\
    run\
    --rm\
    --entrypoint ""\
    -v $(strip $(1))/$(strip $(2)):/work/$(strip $(2))\
    restapi\
    /opt/conda/condabin/conda run -n $(CONDA_ENV_NAME) python /work/$(strip $(2)))
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

define s3_mb
$(call run_docker_compose,\
    run\
    --rm\
    --entrypoint ""\
    mlflow-tracking\
    s3-mb.sh --endpoint-url http://minio:9000 $(strip $(1)))
endef

define s3_sync
$(call run_docker_compose,\
    run\
    --rm\
    --entrypoint ""\
    -v $(strip $(1))/$(strip $(2)):/$(strip $(2))\
    -u $(strip $(call get_host_user_id)):$(strip $(call get_host_group_id))\
    mlflow-tracking\
    s3-sync.sh --endpoint-url http://minio:9000 --delete\
    $(strip $(3)) $(strip $(4)))
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

## Download and prepare MNIST dataset
data: $(TRAINING_DATASET_SENTINEL) $(TESTING_DATASET_SENTINEL)

## Launch the demo
demo: initdb data plugins jupyter workflows services

## Initialize the RESTful API database
initdb: $(RESTAPI_DATABASE)

## Launch the jupyter lab service
jupyter: $(JUPYTER_SENTINEL)

## Synchronize plugins to S3
plugins: $(PLUGINS_SENTINEL)

## Launch the Testbed services
services: $(DOCKER_COMPOSE_SENTINEL)

## Stop and remove the Testbed service containers
teardown: teardown-docker-compose teardown-docker-volumes teardown-docker-compose-sentinel

## Create workflows tarball
workflows: $(WORKFLOWS_TARBALL_FILE)

#################################################################################
# PROJECT SUPPORT RULES                                                         #
#################################################################################

$(EXAMPLE_MINIO_DATA_DIR): ; $(call make_subdirectory,$@) ; $(call chmod,0777,$@)
$(EXAMPLE_MLFLOW_TRACKING_DATA_DIR): ; $(call make_subdirectory,$@) ; $(call chmod,0777,$@)
$(EXAMPLE_REDIS_DATA_DIR): ; $(call make_subdirectory,$@) ; $(call chmod,0777,$@)
$(EXAMPLE_RESTAPI_DATA_DIR): ; $(call make_subdirectory,$@) ; $(call chmod,0777,$@)

$(DOCKER_COMPOSE_SENTINEL): $(PLUGINS_SENTINEL) | $(EXAMPLE_MINIO_DATA_DIR) $(EXAMPLE_MLFLOW_TRACKING_DATA_DIR) $(EXAMPLE_REDIS_DATA_DIR) $(EXAMPLE_RESTAPI_DATA_DIR)
	$(call run_docker_compose,up -d mlflow-tracking nginx redis restapi)
	$(call s3_mb,$(S3_WORKFLOW_BUCKET))
	$(call run_docker_compose,up -d tfcpu-01 tfcpu-02)
	$(call save_sentinel_file,$@)

$(JUPYTER_SENTINEL): | $(EXAMPLE_MINIO_DATA_DIR) $(EXAMPLE_MLFLOW_TRACKING_DATA_DIR) $(EXAMPLE_REDIS_DATA_DIR) $(EXAMPLE_RESTAPI_DATA_DIR)
	$(call chmod,0755,$(JUPYTER_INSTALL_PACKAGES_SCRIPT))
	$(call run_docker_compose,up -d jupyter)
	$(call save_sentinel_file,$@)

$(PLUGINS_SENTINEL): $(PLUGINS_SRC_FILES) | $(EXAMPLE_MINIO_DATA_DIR) $(EXAMPLE_MLFLOW_TRACKING_DATA_DIR) $(EXAMPLE_REDIS_DATA_DIR) $(EXAMPLE_RESTAPI_DATA_DIR)
	$(call s3_mb,$(S3_PLUGINS_BUCKET))
	$(call s3_sync,$(shell dirname $(EXAMPLE_PLUGINS_DIR)),$(shell basename $(EXAMPLE_PLUGINS_DIR)),/$(shell basename $(EXAMPLE_PLUGINS_DIR))/$(shell basename $(PLUGINS_BUILTINS_DIR)),s3://$(S3_PLUGINS_BUCKET)/securingai_builtins)
	$(call run_docker_compose,down)
	$(call docker_remove_volume,$(DOCKER_LOCAL_VOLUMES))
	$(call save_sentinel_file,$@)

$(RESTAPI_DATABASE): $(RESTAPI_DATABASE_INIT_SCRIPT_FILE) | $(EXAMPLE_MINIO_DATA_DIR) $(EXAMPLE_MLFLOW_TRACKING_DATA_DIR) $(EXAMPLE_REDIS_DATA_DIR) $(EXAMPLE_RESTAPI_DATA_DIR)
	$(call init_database,$(EXAMPLE_DIR),$(RESTAPI_DATABASE_INIT_SCRIPT_FILE))
	$(call run_docker_compose,down)
	$(call docker_remove_volume,$(DOCKER_LOCAL_VOLUMES))
	$(RM) -f $(DOCKER_COMPOSE_SENTINEL)

$(TRAINING_DATASET_SENTINEL): $(DATA_DOWNLOAD_FILE) | $(EXAMPLE_MINIO_DATA_DIR) $(EXAMPLE_MLFLOW_TRACKING_DATA_DIR) $(EXAMPLE_REDIS_DATA_DIR) $(EXAMPLE_RESTAPI_DATA_DIR)
	$(call chmod,777,$(EXAMPLE_DATA_DIR))
	$(call download_data,$(EXAMPLE_DIR),$(EXAMPLE_DATA_DIR),--training)
	$(call run_docker_compose,down)
	$(call docker_remove_volume,$(DOCKER_LOCAL_VOLUMES))
	$(call save_sentinel_file,$@)

$(TESTING_DATASET_SENTINEL): $(DATA_DOWNLOAD_FILE) | $(EXAMPLE_MINIO_DATA_DIR) $(EXAMPLE_MLFLOW_TRACKING_DATA_DIR) $(EXAMPLE_REDIS_DATA_DIR) $(EXAMPLE_RESTAPI_DATA_DIR)
	$(call chmod,777,$(EXAMPLE_DATA_DIR))
	$(call download_data,$(EXAMPLE_DIR),$(EXAMPLE_DATA_DIR),--testing)
	$(call run_docker_compose,down)
	$(call docker_remove_volume,$(DOCKER_LOCAL_VOLUMES))
	$(call save_sentinel_file,$@)

$(WORKFLOWS_TARBALL_FILE): $(CODE_SRC_FILES) $(CODE_WORKFLOW_FILE)
	$(call make_tarball,$@,$(CODE_SRC_FILES) $(CODE_WORKFLOW_FILE))
	$(call chmod,644,$(WORKFLOWS_TARBALL_FILE))

teardown-docker-compose:
ifneq ("$(wildcard $(DOCKER_COMPOSE_SENTINEL))","")
	$(call run_docker_compose,down)
else ifneq ("$(wildcard $(JUPYTER_SENTINEL))","")
	$(call run_docker_compose,down)
endif

teardown-docker-volumes:
ifneq ("$(wildcard $(DOCKER_COMPOSE_SENTINEL))","")
	$(call docker_remove_volume,$(DOCKER_LOCAL_VOLUMES))
else ifneq ("$(wildcard $(JUPYTER_SENTINEL))","")
	$(call docker_remove_volume,$(DOCKER_LOCAL_VOLUMES))
endif

teardown-docker-compose-sentinel:
ifneq ("$(wildcard $(DOCKER_COMPOSE_SENTINEL))","")
	$(RM) -f $(DOCKER_COMPOSE_SENTINEL)
endif
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
