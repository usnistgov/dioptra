#!/bin/bash
# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_OPTIONAL_SINGLE([endpoint-url],[],[Endpoint URL for S3 storage],[])
# ARG_POSITIONAL_SINGLE([source],[URI or filepath to a file],[])
# ARG_POSITIONAL_SINGLE([destination],[URI or filepath to a file],[])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Copy file to/from S3 storage\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly destination="${_arg_destination}"
readonly endpoint_url="${_arg_endpoint_url}"
readonly logname="S3 Copy"
readonly source="${_arg_source}"

###########################################################################################
# Copy file to/from S3 storage
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

s3_cp() {
  echo "${logname}: ${source} to ${destination}"

  if [[ ! -z ${endpoint_url} ]]; then
    echo "${logname}: custom endpoint URL ${endpoint_url}"

    aws --endpoint-url ${endpoint_url} s3 cp ${source} ${destination}
  else
    echo "${logname}: default endpoint URL"

    aws s3 cp ${source} ${destination}
  fi
}

###########################################################################################
# Main script
###########################################################################################

s3_cp
# ] <-- needed because of Argbash
