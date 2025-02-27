#!/usr/bin/env bash

### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ###
#######################################################################
### Reset These values if you want to use these default directories ###
export DIOPTRA_CODE="$(HOME)/run-dioptra/dioptra-src"
export DIOPTRA_DEPLOY="$(HOME)/run-dioptra/dioptra-dep"
export DIOPTRA_BRANCH=dev
#######################################################################

export DIOPTRA_VENV=.di-venv-${DIOPTRA_BRANCH}
######## Auto-configuration of the OS-Hardware descriptor
case $(uname) in
    'Linux')
        case $(uname -m) in
            'arm64')
                export DIOPTRA_PLATFORM=linux-arm64
                ;;
            'x86_64')
                export DIOPTRA_PLATFORM=linux-amd64
                ;;
            esac ;;
    'Darwin')
        case $(uname -m) in
            'arm64')
                export DIOPTRA_PLATFORM=macos-arm64
                ;;
            'x86_64')
                export DIOPTRA_PLATFORM=macos-amd64
                ;;
            esac ;;
    esac

######## If you wish to configure something else,   #############
######## Comment/Uncomment/Add/Modify as needed     #############
# DIOPTRA_PLATFORM=linux-arm64
# DIOPTRA_PLATFORM=linux-amd64
# DIOPTRA_PLATFORM=macos-arm64
# DIOPTRA_PLATFORM=macos-amd64

alias frontend='cd ${DIOPTRA_CODE}/src/frontend'

######## Setup REST-API Configuration
export DIOPTRA_RESTAPI_DEV_DATABASE_URI="sqlite:///${DIOPTRA_DEPLOY}/instance/dioptra-dev.db"
export DIOPTRA_RESTAPI_ENV=dev
export DIOPTRA_RESTAPI_VERSION=v1
######## End-of REST-API Configuration

######## Worker Configuration
######## USer-Name and Password Setup
export DIOPTRA_WORKER_USERNAME="dioptra-worker"  # This must be a registered user in the Dioptra app
export DIOPTRA_WORKER_PASSWORD="password"        # Must match the username's password

export DIOPTRA_API="http://localhost:5000"       # This is the default API location when you run `flask run`
export RQ_REDIS_URI="redis://localhost:6379/0"   # This is the default URI when you run `redis-server`
export MLFLOW_S3_ENDPOINT_URL="http://localhost:35000"  # If you're running a MLflow Tracking server, update this to point at it. Otherwise, this is a placeholder.
#export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES   # Macs only, needed to make the RQ worker (i.e. the Dioptra Worker) work
######## End-of Worker Configuration
