#!/bin/bash

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_OPTIONAL_SINGLE([endpoint-url],[],[Endpoint URL for S3 storage],[])
# ARG_POSITIONAL_SINGLE([bucket],[Bucket name],[])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Create bucket on S3 storage backend\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly bucket="${_arg_bucket}"
readonly endpoint_url="${_arg_endpoint_url}"
readonly logname="S3 Make Bucket"

###########################################################################################
# Check if bucket already exists
#
# Globals:
#   bucket
#   endpoint_url
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

s3_bucket_exists() {
  if [[ ! -z ${endpoint_url} ]]; then
    aws --endpoint-url ${endpoint_url} s3api head-bucket --bucket ${bucket}
  else
    aws s3api head-bucket --bucket ${bucket}
  fi
}

###########################################################################################
# Create bucket on S3 storage
#
# Globals:
#   bucket
#   endpoint_url
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

s3_mb() {
  echo "${logname}: Creating bucket s3://${bucket}"

  if [[ ! -z ${endpoint_url} ]]; then
    echo "${logname}: custom endpoint URL ${endpoint_url}"

    [[ -z $(s3_bucket_exists 2>&1) ]] || aws --endpoint-url ${endpoint_url} s3 mb s3://${bucket}
  else
    echo "${logname}: default endpoint URL"

    [[ -z $(s3_bucket_exists 2>&1) ]] || aws s3 mb s3://${bucket}
  fi
}

###########################################################################################
# Main script
###########################################################################################

s3_mb
# ] <-- needed because of Argbash
