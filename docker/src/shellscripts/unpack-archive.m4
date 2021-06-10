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
# ARG_OPTIONAL_BOOLEAN([delete],[d],[Delete archive file after unpacking])
# ARG_POSITIONAL_SINGLE([archive-filepath],[Path to a tarball or zip archive],[])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Unpack archive in current directory\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly archive_filepath="${_arg_archive_filepath}"
readonly bool_delete="${_arg_delete}"
readonly logname="Unpack Archive"

###########################################################################################
# Unpack tarball archive
#
# Globals:
#   logname
# Arguments:
#   Tarball, a path
# Returns:
#   None
###########################################################################################

untar_file() {
  local archive_dir="$(dirname $1)"
  local archive_file="$(basename $1)"

  echo "${logname}: untar ${archive_file} into ${archive_dir}"

  bash -c "cd ${archive_dir} && tar xf ${archive_file}"
}

###########################################################################################
# Unpack zip archive
#
# Globals:
#   logname
# Arguments:
#   Zip archive, a path
# Returns:
#   None
###########################################################################################

unzip_file() {
  local archive_dir="$(dirname $1)"
  local archive_file="$(basename $1)"

  echo "${logname}: unzip ${archive_file} into ${archive_dir}"

  bash -c "cd ${archive_dir} && unzip ${archive_file}"
}

###########################################################################################
# Unpack an archive
#
# Globals:
#   archive_filepath
#   bool_delete
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

unpack_archive() {
  case ${archive_filepath} in
    *.tar | *.tar.bz2 | *.tar.gz | *.tar.xz | *.tgz)
      untar_file ${archive_filepath}
      if [[ ${bool_delete} == on ]]; then
        rm ${archive_filepath}
      fi
      ;;
    *.zip)
      unzip_file ${archive_filepath}
      if [[ ${bool_delete} == on ]]; then
        rm ${archive_filepath}
      fi
      ;;
    *)
      echo "${logname}: WARNING - unsupported file format - $(basename ${archive_filepath})" 1>&2
      ;;
  esac
}

###########################################################################################
# Main script
###########################################################################################

unpack_archive
# ] <-- needed because of Argbash
