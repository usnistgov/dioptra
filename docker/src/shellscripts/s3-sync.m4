#!/bin/bash

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_OPTIONAL_SINGLE([endpoint-url],[],[Endpoint URL for S3 storage],[])
# ARG_POSITIONAL_SINGLE([source],[URI or path to a directory],[])
# ARG_POSITIONAL_SINGLE([destination],[URI or path to a directory],[])
# ARG_OPTIONAL_BOOLEAN([delete],[],[Files that exist in the destination but not in the source are deleted during sync],[])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Synchronize directories to/from S3 storage\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly delete="${_arg_delete}"
readonly destination="${_arg_destination}"
readonly endpoint_url="${_arg_endpoint_url}"
readonly logname="S3 Sync"
readonly source="${_arg_source}"

###########################################################################################
# Set option flags to pass to aws s3 sync
#
# Globals:
#   delete
# Arguments:
#   None
# Returns:
#   prepared option flags
###########################################################################################

set_options() {
  local opts=""

  [[ ${delete} == off ]] || opts+="--delete "

  echo ${opts}
}

###########################################################################################
# Sync directory to/from S3 storage
#
# Globals:
#   destination
#   endpoint_url
#   logname
#   source
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

s3_sync() {
  local opts=$(set_options)

  echo "${logname}: ${source} to ${destination}"
  echo "${logname}: option flags: ${opts}"

  if [[ ! -z ${endpoint_url} ]]; then
    echo "${logname}: custom endpoint URL ${endpoint_url}"

    aws --endpoint-url ${endpoint_url} s3 sync ${source} ${destination} ${opts}
  else
    echo "${logname}: default endpoint URL"

    aws s3 sync ${source} ${destination} ${opts}
  fi
}

###########################################################################################
# Main script
###########################################################################################

s3_sync
# ] <-- needed because of Argbash
