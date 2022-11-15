#!/bin/bash
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
