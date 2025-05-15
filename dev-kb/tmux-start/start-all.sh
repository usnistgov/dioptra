#!/usr/bin/env bash

###########################################################################################
### Prints usage information for the script 
###
###  Globals: None
###  Arguments: None
###  Returns:
###    Message in terminal
###########################################################################################

print_main_help()
{
    src_path="${BASH_SOURCE[0]}"
    exec_path="$0"
    this_name=$(basename "$src_path")

    printf "\n Please use the application with configuration file provided as an input parameter:
    \n  >${this_name} [--environment|--env|-e] <environment-file>
    \t<environment-file> - File containing environment configuration
    \n\tExamples:
    \t Start tmux server using local to script './start-all.sh' config file './env1.cfg':
    \t   >./${this_name} -e ./env1.cfg
    
    \t Start tmux server using file located in another co-located directory '../local-setup/env-demo.cfg':
    \t   >./dev-kb/tmux-start-all/${this_name} -e ./dev-kb/local-setup/env-demo.cfg\n\n"
}

###########################################################################################
### Read and initialize the script's input parameter
###
###  Globals:
###     Sets following environment variables 
###     (if they exist in the environment file):
###         DIOPTRA_BRANCH
###         DIOPTRA_CODE
###         DIOPTRA_DEPLOY
###         DIOPTRA_CONFIG_INFO
###         DIOPTRA_ENV_NAME
###  Arguments:
###    Environment config-file
###  Returns:
###    Changes to the global environment-variables
###########################################################################################
read_properties_from_file()
{
  file="$1"
  echo "Reading environment from config file: $file"

  while IFS="=" read -r key value; do
    case "${key}" in
      "DIOPTRA_GIT_BRANCH") 
        export DIOPTRA_BRANCH="$value"
        ;;
      "DIOPTRA_CODE_DIR") 
        ### Expand ~/ path just in-case it wasn't fully resolved
        export DIOPTRA_CODE="${value/#\~/$HOME}" 
        ;;
      "DIOPTRA_DEPLOY_DIR") 
        ### Expand ~/ path just in-case it wasn't fully resolved
        export DIOPTRA_DEPLOY="${value/#\~/$HOME}"
        ;;
      "DIOPTRA_CONFIG_INFO")
        export DIOPTRA_CONFIG_INFO="$value"
        ;;
      "DIOPTRA_ENV_NAME")
        export DIOPTRA_ENV_NAME="$value"
        ;;      \#*)
        ### printf "\nComment: [key:${key} value:${value}]\n"
        ;;
      *)
        ### printf "\nIgnoring Entry: [key:${key} value:${value}]\n"
        ;;
    esac
    # printf "\nKey=$key;\tValue=$value"
  done < "$file"
  # printf "\n\n"
}

###########################################################################################
### Read and initialize the script's input parameter
###
###  Globals:
###     Sets DIOPTRA_CONF_FILE and DIOPTRA_CONF_REAL_PATH if the value was provided
###  Arguments:
###    Error messages to log, one or more strings
###  Returns:
###    None
###########################################################################################
read_init_parameters()
{
  while [ $# -gt 0 ]; do
    echo
    echo "Input Parameters: Key: ${1@Q}; Value: ${2@Q};"
    echo
    case "$1" in
      --environment|--env|-e)
        export DIOPTRA_CONF_FILE="${2}"
        export DIOPTRA_CONF_REAL_PATH="$(realpath ${2})"
        shift
        break
        ;;

      *)
        printf "Error: Incorrect Parameter [${1} ${2}]\n"
        ### return 1
        shift
        ;;

    esac
    shift
  done
}

###########################################################################################
### After the session was initialized set up TMux to behave reasonably
###
###  Globals:
###     Changes tmux behavior
###  Arguments:
###    None
###  Returns:
###    Reasonably configured TMux server as side-effect
###########################################################################################
setup_tmux(){
    # Allow to tag the panes in the window to make clear what's running where
    tmux set pane-border-status bottom # alternatively can be set to [bottom], but [top] looks more intuitive
    tmux set pane-border-format "┤ #{pane_index}. #{pane_title} ├" # Format the panel
    tmux set-option mouse on  # Activate on-mouse pane flipping in addition to "Ctrl+B and Arrows"
    # Show the environment variables visible to tmux (info-value)
    tmux send-keys "env"  'C-m'
}

###########################################################################################
### Decide context in which to run TMux and the servers start-up scripts
### 
###  Globals:
###     NONE
###  Arguments:
###    Error messages to log, one or more strings
###  Returns:
###    None
###########################################################################################
decide_dioptra_environment(){
    ###
    SCRIPT_SOURCE="$(realpath ${BASH_SOURCE[0]})"
    DIOPTRA_CONF_RP="$(realpath $DIOPTRA_CONF_FILE)" 
    CURRENT_DOT_PATH="$(realpath ./)"

    tmux_dir_name="tmux-start"
    parent_dir="$(basename $(dirname ${SCRIPT_SOURCE}))"

    # Useful code chunks for debugging in case new functionality needs to be added 
    # echo "!!!!!!!!!!!!!!!!!!!!!!!!!!"
    # echo "TMX-Dir = ${tmux_dir_name@Q}"
    # echo "PAR-Dir = ${parent_dir@Q}"
    # echo "!!!!!!!!!!!!!!!!!!!!!!!!!!"

    ### Decide to run all scripts from same place or from the GitHub repo locations
    if ! [ "${tmux_dir_name}" == "${parent_dir}" ]; then
        ### Set up environment to run local all-in-one place scripts
        echo "==============================================="
        echo "Configured to run in ALL-LOCAL-MODE"
        echo "==============================================="
        echo "Running from path: ${SCRIPT_SOURCE}/"
        echo "==============================================="
        export DIOPTRA_ML_FLOW="."
        export DIOPTRA_LOCAL="."
    else
        ### Set up environment to run from GitHub repo default locations scripts
        echo "==============================================="
        echo "Configured to run in DEFAULT-MODE"
        echo "==============================================="
        echo "Running from path: ${SCRIPT_SOURCE}/"
        echo "Using the following script Locations:"
        echo "  ${DIOPTRA_CODE}/dev-kb/tmux-start/*.sh"
        echo "  ${DIOPTRA_CODE}/dev-kb/local-setup/*.sh"
        echo "  ${DIOPTRA_CODE}/dev-kb/ml-flow/*.sh"
        echo "==============================================="
        export DIOPTRA_ML_FLOW="${DIOPTRA_CODE}/dev-kb/ml-flow"
        export DIOPTRA_LOCAL="${DIOPTRA_CODE}/dev-kb/local-setup"
    fi
    dir="$(realpath ${DIOPTRA_CODE})"
    echo "DIR=${dir}"

    ml_dir="${dir}/mlflow-${DIOPTRA_BRANCH}"
    export DIOPTRA_MLF_ART="${ml_dir}/art"
    export DIOPTRA_MLF_SQL="sqlite:///${ml_dir}/mlflow-${DIOPTRA_BRANCH}.sqlite" 
    echo "DIOPTRA_MLF_ART=${DIOPTRA_MLF_ART} DIOPTRA_MLF_SQL=${DIOPTRA_MLF_SQL}"
    # Useful code chunks for debugging in case new functionality needs to be added 
    # echo "!!!!!!!!!!!!!!!!!!!!!!!!!!"
    # echo "MLF = ${DIOPTRA_ML_FLOW@Q}"
    # echo "LRP = ${DIOPTRA_LOCAL@Q}"
    # echo "./-Path = ${DIOPTRA_DOT_PATH@Q}"
    # echo "TM-Dir = ${tmux_dir_name@Q}"
    # echo "PD-Dir = ${parent_dir@Q}"
    # echo "!!!!!!!!!!!!!!!!!!!!!!!!!!"

    # Initialize the original environment for DIOPTRA 
    source "${DIOPTRA_LOCAL}/dev-set.sh" -e "${DIOPTRA_CONF_FILE}"
    sh "${DIOPTRA_LOCAL}/setup.sh"
}

###########################################################################################
###########################################################################################
### 
### Begin the main script body
### 
###########################################################################################
###########################################################################################
read_init_parameters $@
echo "DCF = $DIOPTRA_CONF_FILE"
echo "DCRP = $DIOPTRA_CONF_REAL_PATH"
echo
# test -z "${DIOPTRA_CONF_FILE}"
# echo "TEST-non-empty: $? ${DIOPTRA_CONF_FILE@Q}"
# test -e "${DIOPTRA_CONF_FILE@Q}"
# echo "TEST-exists: $?  ${DIOPTRA_CONF_FILE@Q}"
# test -f "${DIOPTRA_CONF_FILE@Q}" 
# echo "TEST-file: $?  ${DIOPTRA_CONF_FILE@Q}" 

if ! [ -z "${DIOPTRA_CONF_FILE}" ] && ! [ -z "${DIOPTRA_CONF_REAL_PATH}" ] ; then

    if ! [ -e "${DIOPTRA_CONF_REAL_PATH}" ]; then
        echo "File ${DIOPTRA_CONF_REAL_PATH@Q} doesn't exist"
        exit -1
    fi
    if ! [ -f "${DIOPTRA_CONF_REAL_PATH}" ] ; then
        echo "${DIOPTRA_CONF_REAL_PATH@Q} isn't a file"
        exit -1
    fi

    read_properties_from_file "${DIOPTRA_CONF_REAL_PATH}"
    decide_dioptra_environment

    ### TODO: remove the SET-ENV debugging statement below
    # exit 0

    # Begin talking to tmux server and create a new session
    tmux new-session -d -s di-all
    setup_tmux

    # 0. Set up and name Flask pane
    tmux select-pane -t 0 -T 'Flask'
    tmux send-keys "${DIOPTRA_LOCAL}/run-flask.sh" 'C-m'

    # 1. Split out, set up, and name Redis pane
    tmux split-window -v -t 0
    tmux select-pane -t 1 -T 'Redis'
    tmux send-keys "${DIOPTRA_LOCAL}/run-redis.sh" 'C-m'

    # 2. Split out, set up, and name Worker pane 
    tmux split-window -v -t 1
    tmux select-pane -t 2 -T 'Worker'
    tmux send-keys 'sleep 2.2' 'C-m' # Artificial delay to wait for Redis readiness
    tmux send-keys "${DIOPTRA_LOCAL}/run-worker.sh" 'C-m'

    # Even Up the panes heights
    tmux select-layout even-vertical

    # 3. Split out, set up, and name Front-End pane 
    tmux split-window -h -l 66% -t 2
    tmux select-pane -t 3 -T 'Front-End'
    tmux send-keys "${DIOPTRA_LOCAL}/run-front.sh" 'C-m'

    # 4. Split out, set up, and name MLFlow pane
    tmux split-window -h -l 50% -t 3
    tmux select-pane -t 4 -T 'MLFlow'
    tmux send-keys "source ${DIOPTRA_CODE}/${DIOPTRA_VENV}/bin/activate" 'C-m'
    tmux send-keys "${DIOPTRA_ML_FLOW}/start-mlflow.sh --artifacts-destination ${DIOPTRA_MLF_ART} --backend-store-uri ${DIOPTRA_MLF_SQL} --port 35000" 'C-m'

    tmux -2 attach-session -t di-all
else
    echo
    echo "!!! The input parameter --environment|--env|-e was not properly provided !!!"
    print_main_help
fi
