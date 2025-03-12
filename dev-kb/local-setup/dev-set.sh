#!/usr/bin/env bash

print_env_status(){
  printf "\n\nDIOPTRA environment variables are set as follows:\n\n" 
  env | sort | grep DIOPTRA
  printf "\nUse 'env | sort', 'env | sort | grep DIOPTRA', or 'printenv' to view the rest of the environment variables\n\n"
}

print_main_help()
{
    src_path="${BASH_SOURCE[0]}"
    exec_path="$0"
    ### Useful for checking if script was sourced or executed
    # if [ "${src_path^^}" != "${exec_path^^}" ]; then
    #   printf "Cx2[SOURCED]: [${src_path^^}] =?= [${exec_path^^}]\n"
    # else
    #   printf "Cx1:[COMMANDED] [${src_path^^}] =?= [${exec_path^^}]\n"
    # fi
    this_name=$(basename "$src_path")

    printf "\nHow to use ${this_name} script:\n
    \t1. Explicitly specify fully specified Src and Work directories and GitHub tag:\n
    \t>source ${this_name} [--tag|-t] <github_tag> [--work|-w] <work_dir> [--source|-s] <source_dir>\n
    \t\t<github_tag>\t\t Branch-Name that takes values dev|main|<existing-git-branch>
    \t\t<work_dir>\t\t Directory to use as working deployment
    \t\t<source_dir>\t\t Directory to use as the storage for source
    \n\tExample: INITIALIZE ENVIRONMENT with environment settings used inline:
    \t>source ./dev-env+.sh -t dev -w ~/di2run/dio-wrk -s ~/di2run/dio-src"


    printf "\n\n\t2. Explicitly request use of the Default Dirs at current working directory and GitHub tag:
    \n\t>source ${this_name} [--env|-e] <environment-file>
    \n\t\t<environment-file>\t File containing environment configuration
    \n\tExample: INITIALIZE ENVIRONMENT with key-value-pairs environment file:
    \t>source ./dev-env+.sh -e ./env-example1.cfg\n\n"
}

set_display_env_details(){
  ### Set a reminder variable to track where the environment originated from. 
  if [ -v "$DIOPTRA_CONFIG_INFO" ]; then 
      export DIOPTRA_CONFIG_DETAILS="
      Dioptra Environment was Built from:
      \tfile: $DIOPTRA_ENV_FILE 
      \tbranch-id:\t$DIOPTRA_BRANCH
      \tcode-dir:\t$DIOPTRA_CODE
      \tdeploy-dir:\t$DIOPTRA_DEPLOY
      \n"
  else
      ### Config info was not supplied
      export DIOPTRA_CONFIG_DETAILS="        
      Dioptra Environment was Built with:
      \tenv-info:\t$DIOPTRA_CONFIG_INFO
      \tenv-file:\t$DIOPTRA_ENV_FILE 
      \tbranch-id:\t$DIOPTRA_BRANCH
      \tcode-dir:\t$DIOPTRA_CODE
      \tdeploy-dir:\t$DIOPTRA_DEPLOY
      \n"
  fi
  printf "To recall "Environment Info:" below use command: printf \"\${DIOPTRA_CONFIG_DETAILS}\"\nEnvironment Info:$DIOPTRA_CONFIG_DETAILS\n"
}

read_properties_from_file()
{
  file="$1"
  echo "Reading environment from config file: $file"

  while IFS="=" read -r key value; do
    case "${key^^}" in
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
      \#*)
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


print_env_variables()
{
  printf "\nThe following Parameters were expected:\n"
  printf "DIOPTRA_BRANCH=$DIOPTRA_BRANCH\n"
  printf "DIOPTRA_DEPLOY=$DIOPTRA_DEPLOY\n"
  printf "DIOPTRA_CODE=$DIOPTRA_CODE\n"
  printf "or\n"
  printf "DIOPTRA_ENV_FILE=$DIOPTRA_ENV_FILE\n"
}
########################################################################################
######## Iterates through CLI parameters and sets them as environment variables ########
######## In case the variable is file - the values form file set in environment ########
read_cli_parameters()
{

  ## Print all arguments, each as a separate word
  # echo "Arguments as separate words: $*"

  ## Print all arguments, each as a separate string (handles spaces correctly)
  # echo "Arguments as separate strings: $@"

  ## Print the number of arguments
  # echo "Number of arguments: $#"

  # Print each argument with its index
  # for i in $(seq 0 $(($# - 1))); do
  #   echo "Argument $i: ${!i}"
  # done


  while [ $# -gt 0 ]; do
    printf "\n $1 - $2"
    case "$1" in
      --tag|-t)
        export DIOPTRA_BRANCH="${2}"
        shift
        ;;
      --deploy|--dep|--work|--wrk|-d|-w)
        export DIOPTRA_DEPLOY="${2}"
        shift
        ;;
      --source|--src|-s)
        export DIOPTRA_CODE="${2}"
        shift
        ;;
      --environment|--env|-e)
        export DIOPTRA_ENV_FILE="${2}"
        read_properties_from_file $DIOPTRA_ENV_FILE
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
##################################################################################
### Script Main-Body
##################################################################################
### Make sure that we begin with clean environment variables to avoid hybrid swamp
unset DIOPTRA_ENV_FILE
unset DIOPTRA_BRANCH
unset DIOPTRA_CODE
unset DIOPTRA_DEPLOY
unset DIOPTRA_CONFIG_INFO
unset DIOPTRA_CONFIG_DETAILS


# if [ -n "${BASH_VERSION}" ]; then
#   printf "\nStarting script with BASH Version: ${BASH_VERSION}\n"
# else
#   printf "\n❌❌❌ BASH is required to run this script ❌❌❌\n"
#   return
# fi
##################################################################################
######## In case no parameters were provided tell how to use and bail out ########
if [ $# -eq 0 ]; then
  print_main_help
  printf "\n❌❌❌ !!!Please use parameters as described above!!! ❌❌❌"
  return 1  
fi

############################################
### Run the main parameter-reading logic ###
read_cli_parameters $@


if [ -z "$DIOPTRA_BRANCH" ] || [ -z "$DIOPTRA_CODE" ] || [ -z "$DIOPTRA_DEPLOY" ]; then
  print_main_help
  printf "\n❌❌❌ !!!Failed to set up environment configuration!!! ❌❌❌
  \t\t Please, Read Usage Guide Above
  "  
  ## Can be helpful for debugging
  ## print_env_variables
  echo "Then you can use 'env | sort' or 'printenv' command to view the rest of the environment variables"

else
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


  printf "\n Working from the path $(pwd)\n"

  printf "\n Script works with GitHub BRANCH:\t $DIOPTRA_BRANCH"
  printf "\n Script assumes GitHub repo in SRC-DIR:\t $DIOPTRA_CODE"
  printf "\n Script assumes DIOPTRA deployed to Work-DIR:\t $DIOPTRA_DEPLOY\n\n"

  print_env_status
  set_display_env_details
fi


