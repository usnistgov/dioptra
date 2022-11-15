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
#
# The parse_* functions are adapted from the following source:
#
#     Patryk Obara (https://stackoverflow.com/users/2033752/patryk-obara), Parse URL
#         in shell script, URL (version: 2017-08-31):
#         https://stackoverflow.com/q/45977232
#
# The regular expression in URI_REGEX is taken from:
#
#     scott (https://stackoverflow.com/users/1771778/scott), Parse URL in shell script,
#         URL (version: 2020-09-21): https://stackoverflow.com/q/63993578

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_POSITIONAL_SINGLE([uri],[URI],[])
# ARG_OPTIONAL_BOOLEAN([scheme],[],[Print the 'scheme' field of URI],[])
# ARG_OPTIONAL_BOOLEAN([authority],[],[Print the 'authority' field of URI],[])
# ARG_OPTIONAL_BOOLEAN([user],[],[Print the 'user' field of URI],[])
# ARG_OPTIONAL_BOOLEAN([host],[],[Print the 'host' field of URI],[])
# ARG_OPTIONAL_BOOLEAN([port],[],[Print the 'port' field of URI],[])
# ARG_OPTIONAL_BOOLEAN([path],[],[Print the 'path' field of URI],[])
# ARG_OPTIONAL_BOOLEAN([rpath],[],[Print the 'rpath' field of URI],[])
# ARG_OPTIONAL_BOOLEAN([query],[],[Print the 'query' field of URI],[])
# ARG_OPTIONAL_BOOLEAN([fragment],[],[Print the 'fragment' field of URI],[])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Extract a field from a URI\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly uri="${_arg_uri}"
readonly scheme="${_arg_scheme}"
readonly authority="${_arg_authority}"
readonly user="${_arg_user}"
readonly host="${_arg_host}"
readonly port="${_arg_port}"
readonly path="${_arg_path}"
readonly rpath="${_arg_rpath}"
readonly query="${_arg_query}"
readonly fragment="${_arg_fragment}"
readonly logname="Parse URI"
readonly URI_REGEX='^(([^:/?#]+):)?(//((([^:/?#]+)@)?([^:/?#]+)(:([0-9]+))?))?((/|$)([^?#]*))(\?([^#]*))?(#(.*))?$'

###########################################################################################
# Validate the option flags to ensure no more than one field is extracted at a time
#
# Globals:
#   scheme
#   authority
#   user
#   host
#   port
#   path
#   rpath
#   query
#   fragment
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_option_flags() {
  local num_options=0

  for field in ${scheme} ${authority} ${user} ${host} ${port} ${path} ${rpath} ${query} ${fragment}; do
    [[ ${field} == off ]] || ((num_options += 1))
  done

  if [[ ${num_options} > 1 ]]; then
    echo "${logname}: ERROR - More than one field selected" 1>&2
    exit 1
  fi
}

###########################################################################################
# Extract the 'scheme' field from URI
#
# Globals:
#   URI_REGEX
# Arguments:
#   None
# Returns:
#   extracted scheme field
###########################################################################################

parse_scheme() {
  [[ "${uri}" =~ $URI_REGEX ]] && echo "${BASH_REMATCH[2]}"
}

###########################################################################################
# Extract the 'authority' field from URI
#
# Globals:
#   URI_REGEX
# Arguments:
#   None
# Returns:
#   extracted authority field
###########################################################################################

parse_authority() {
  [[ "${uri}" =~ $URI_REGEX ]] && echo "${BASH_REMATCH[4]}"
}

###########################################################################################
# Extract the 'user' field from URI
#
# Globals:
#   URI_REGEX
# Arguments:
#   None
# Returns:
#   extracted user field
###########################################################################################

parse_user() {
  [[ "${uri}" =~ $URI_REGEX ]] && echo "${BASH_REMATCH[6]}"
}

###########################################################################################
# Extract the 'host' field from URI
#
# Globals:
#   URI_REGEX
# Arguments:
#   None
# Returns:
#   extracted host field
###########################################################################################

parse_host() {
  [[ "${uri}" =~ $URI_REGEX ]] && echo "${BASH_REMATCH[7]}"
}

###########################################################################################
# Extract the 'port' field from URI
#
# Globals:
#   URI_REGEX
# Arguments:
#   None
# Returns:
#   extracted port field
###########################################################################################

parse_port() {
  [[ "${uri}" =~ $URI_REGEX ]] && echo "${BASH_REMATCH[9]}"
}

###########################################################################################
# Extract the 'path' field from URI
#
# Globals:
#   URI_REGEX
# Arguments:
#   None
# Returns:
#   extracted path field
###########################################################################################

parse_path() {
  [[ "${uri}" =~ $URI_REGEX ]] && echo "${BASH_REMATCH[10]}"
}

###########################################################################################
# Extract the 'rpath' field from URI
#
# Globals:
#   URI_REGEX
# Arguments:
#   None
# Returns:
#   extracted rpath field
###########################################################################################

parse_rpath() {
  [[ "${uri}" =~ $URI_REGEX ]] && echo "${BASH_REMATCH[11]}"
}

###########################################################################################
# Extract the 'query' field from URI
#
# Globals:
#   URI_REGEX
# Arguments:
#   None
# Returns:
#   extracted query field
###########################################################################################

parse_query() {
  [[ "${uri}" =~ $URI_REGEX ]] && echo "${BASH_REMATCH[13]}"
}

###########################################################################################
# Extract the 'fragment' field from URI
#
# Globals:
#   URI_REGEX
# Arguments:
#   None
# Returns:
#   extracted fragment field
###########################################################################################

parse_fragment() {
  [[ "${uri}" =~ $URI_REGEX ]] && echo "${BASH_REMATCH[15]}"
}

###########################################################################################
# Parse URI and extract a field
#
# Globals:
#   scheme
#   authority
#   user
#   host
#   port
#   path
#   rpath
#   query
#   fragment
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

parse_uri() {
  case "on" in
    ${scheme})
      parse_scheme
      ;;
    ${authority})
      parse_authority
      ;;
    ${user})
      parse_user
      ;;
    ${host})
      parse_host
      ;;
    ${port})
      parse_port
      ;;
    ${path})
      parse_path
      ;;
    ${rpath})
      parse_rpath
      ;;
    ${query})
      parse_query
      ;;
    ${fragment})
      parse_fragment
      ;;
    *)
      echo "${logname}: ERROR - No field selected" 1>&2
      exit 1
      ;;
  esac
}

###########################################################################################
# Main script
###########################################################################################

validate_option_flags
parse_uri
# ] <-- needed because of Argbash
