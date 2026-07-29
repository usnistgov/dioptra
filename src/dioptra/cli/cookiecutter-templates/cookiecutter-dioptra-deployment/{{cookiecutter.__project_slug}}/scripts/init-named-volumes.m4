#!/usr/bin/env bash
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
# ARG_OPTIONAL_SINGLE([scripts-dir],[],[Path to directory with processed init scripts],[/scripts])
# ARG_OPTIONAL_SINGLE([config-dir],[],[Path to config directory mounted from host],[/config])
# ARG_OPTIONAL_SINGLE([secrets-dir],[],[Path to secrets directory mounted from host],[/secrets])
# ARG_OPTIONAL_SINGLE([ssl-dir],[],[Path to ssl directory mounted from host],[/ssl])
# ARG_OPTIONAL_SINGLE([clone-branch],[],[The dioptra branch to clone and use for syncing task plugins],[main])
# ARG_OPTIONAL_SINGLE([chown-mc],[],[File ownership setting for the user in the mc image],[root:root])
# ARG_OPTIONAL_SINGLE([chown-minio],[],[File ownership setting for the user in the minio image],[root:root])
# ARG_OPTIONAL_SINGLE([chown-mlflow],[],[File ownership setting for the non-root user in mlflow-tracking image],[39000:100])
# ARG_OPTIONAL_SINGLE([chown-nginx],[],[File ownership setting for the non-root user in nginx image],[39000:100])
# ARG_OPTIONAL_SINGLE([chown-dbadmin],[],[File ownership setting for the non-root user in dbamin image],[5050:5050])
# ARG_OPTIONAL_SINGLE([chown-postgres],[],[File ownership setting for the non-root user in postgres image],[999:999])
# ARG_OPTIONAL_SINGLE([chown-redis],[],[File ownership setting for the non-root user in redis image],[999:999])
# ARG_OPTIONAL_SINGLE([chown-restapi],[],[File ownership setting for the non-root user in restapi image],[39000:100])
# ARG_OPTIONAL_SINGLE([init-repos-dir],[],[Path to the directory for the init-repos named volume],[/volumes/init-repos])
# ARG_OPTIONAL_SINGLE([postgres-initdb-d-dir],[],[Path to the directory for the postgres-docker-entrypoint-initdb-d named volume],[/volumes/postgres-docker-entrypoint-initdb-d])
# ARG_OPTIONAL_SINGLE([postgres-etc-postgresql-dir],[],[Path to the directory for the postgres-etc-postgresql named volume],[/volumes/postgres-etc-postgresql])
# ARG_OPTIONAL_SINGLE([postgres-var-certs-dir],[],[Path to the directory for the postgres-var-certs named volume],[/volumes/postgres-var-certs])
# ARG_OPTIONAL_SINGLE([mc-ca-certificates-dir],[],[Path to the directory for the mc-ca-certificates named volume],[/volumes/mc-ca-certificates])
# ARG_OPTIONAL_SINGLE([minio-certs-dir],[],[Path to the directory for the minio-certs named volume],[/volumes/minio-certs])
# ARG_OPTIONAL_SINGLE([minio-data-dir],[],[Path to the directory for the minio-data named volume],[/volumes/minio-data])
# ARG_OPTIONAL_SINGLE([dbadmin-certs-dir],[],[Path to the directory for the dbadmin-certs named volume],[/volumes/dbadmin-ca-certificates])
# ARG_OPTIONAL_SINGLE([dbadmin-data-dir],[],[Path to the directory for the dbadmin-data named volume],[/volumes/dbadmin-data])
# ARG_OPTIONAL_SINGLE([nginx-conf-d-dir],[],[Path to the directory for the nginx-conf-d named volume],[/volumes/nginx-conf-d])
# ARG_OPTIONAL_SINGLE([nginx-etc-ssl-dir],[],[Path to the directory for the nginx-etc-ssl named volume],[/volumes/nginx-etc-ssl])
# ARG_OPTIONAL_SINGLE([redis-data-dir],[],[Path to the directory for the redis-data named volume],[/volumes/redis-data])
# ARG_OPTIONAL_BOOLEAN([enable-nginx-ssl],[],[Enable the SSL-enabled configuration settings for nginx image])
# ARG_OPTIONAL_BOOLEAN([enable-postgres-ssl],[],[Enable the SSL-enabled configuration settings for postgres image])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Utility script that prepares the deployment's named volumes.\n])
# ARGBASH_GO()

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

LOGNAME="Init Named Volumes"
DIOPTRA_GIT_REPO_URL="https://github.com/usnistgov/dioptra.git"

###########################################################################################
# Print an error log message to stderr
#
# Globals:
#   LOGNAME
# Arguments:
#   Error messages to log, one or more strings
# Returns:
#   None
###########################################################################################

log_error() {
  echo "${LOGNAME}: ERROR -" "${@}" 1>&2
}

###########################################################################################
# Print an informational log message to stdout
#
# Globals:
#   LOGNAME
# Arguments:
#   Info messages to log, one or more strings
# Returns:
#   None
###########################################################################################

log_info() {
  echo "${LOGNAME}: INFO -" "${@}"
}

###########################################################################################
# Create a directory, including missing parent directories, if it doesn't exist
#
# Globals:
#   None
# Arguments:
#   Directory to be created, a path
#   umask value to use when creating directories, a four-digit octal
# Returns:
#   None
###########################################################################################

create_dir() {
  local dir_path="${1}"
  local umask_value="${2}"

  log_info "Creating the directory ${dir_path} if it does not exist"

  if ! (umask "${umask_value}" && mkdir -p "${dir_path}"); then
    log_error "Creating the directory ${dir_path} failed"
    exit 1
  fi
}

###########################################################################################
# Recursively remove all files within a directory
#
# Globals:
#   None
# Arguments:
#   Directory to be cleared, a path
# Returns:
#   None
###########################################################################################

clear_dir() {
  local dir_path="${1}"

  log_info "Clearing the directory ${dir_path}"

  if ! rm -vrf ${dir_path}; then
    log_error "Clearing the directory ${dir_path} failed"
    exit 1
  fi
}

###########################################################################################
# Wrapper for the copy-extra-ca-certificates.sh utility script
#
# Globals:
#   _arg_scripts_dir
# Arguments:
#   Positional arguments for the script, one or more strings
# Returns:
#   None
###########################################################################################

copy_extra_ca_certificates() {
  if ! "${_arg_scripts_dir}/copy-extra-ca-certificates.sh" "${@}"; then
    log_error "Encountered an error when executing" \
      "${_arg_scripts_dir}/copy-extra-ca-certificates.sh, exiting..."
    exit 1
  fi
}

###########################################################################################
# Wrapper for the file-copy.sh utility script
#
# Globals:
#   _arg_scripts_dir
# Arguments:
#   Positional arguments for the script, one or more strings
# Returns:
#   None
###########################################################################################

file_copy() {
  if ! "${_arg_scripts_dir}/file-copy.sh" "${@}"; then
    log_error "Encountered an error when executing ${_arg_scripts_dir}/file-copy.sh," \
      "exiting..."
    exit 1
  fi
}

###########################################################################################
# Wrapper for the git-clone.sh utility script
#
# Globals:
#   _arg_scripts_dir
# Arguments:
#   Positional arguments for the script, one or more strings
# Returns:
#   None
###########################################################################################

git_clone() {
  if ! "${_arg_scripts_dir}/git-clone.sh" "${@}"; then
    log_error "Encountered an error when executing ${_arg_scripts_dir}/git-clone.sh," \
      "exiting..."
    exit 1
  fi
}

###########################################################################################
# Wrapper for the globbed-copy.sh utility script
#
# Globals:
#   _arg_scripts_dir
# Arguments:
#   Positional arguments for the script, one or more strings
# Returns:
#   None
###########################################################################################

globbed_copy() {
  if ! "${_arg_scripts_dir}/globbed-copy.sh" "${@}"; then
    log_error "Encountered an error when executing ${_arg_scripts_dir}/globbed-copy.sh," \
      "exiting..."
    exit 1
  fi
}

###########################################################################################
# Wrapper for the set-permissions.sh utility script
#
# Globals:
#   _arg_scripts_dir
# Arguments:
#   Positional arguments for the script, one or more strings
# Returns:
#   None
###########################################################################################

set_permissions() {
  if ! "${_arg_scripts_dir}/set-permissions.sh" "${@}"; then
    log_error "Encountered an error when executing" \
      "${_arg_scripts_dir}/set-permissions.sh, exiting..."
    exit 1
  fi
}

###########################################################################################
# Prepares the named volumes used by the nginx image
#
# Globals:
#   _arg_chown_nginx
#   _arg_config_dir
#   _arg_ssl_dir
#   _arg_nginx_conf_d_dir
#   _arg_nginx_etc_ssl_dir
#   _arg_enable_nginx_ssl
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

prepare_nginx_volumes() {
  clear_dir "${_arg_nginx_conf_d_dir}/*"

  set_permissions --dir-chmod "0755" --chown "${_arg_chown_nginx}" \
    "${_arg_nginx_conf_d_dir}"

  if [[ "${_arg_enable_nginx_ssl}" == "on" ]]; then
    globbed_copy --chmod "0644" --chown "${_arg_chown_nginx}" \
      "${_arg_config_dir}/nginx" "${_arg_nginx_conf_d_dir}" 'https_*.conf'

    globbed_copy --chmod "0644" --chown "${_arg_chown_nginx}" \
      "${_arg_ssl_dir}/nginx" "${_arg_nginx_etc_ssl_dir}" '*.crt'

    globbed_copy --chmod "0600" --chown "${_arg_chown_nginx}" \
      "${_arg_ssl_dir}/nginx" "${_arg_nginx_etc_ssl_dir}" '*.key'
  else
    globbed_copy --chmod "0644" --chown "${_arg_chown_nginx}" \
      "${_arg_config_dir}/nginx" "${_arg_nginx_conf_d_dir}" 'http_*.conf'
  fi

  globbed_copy --chmod "0644" --chown "${_arg_chown_nginx}" \
    "${_arg_config_dir}/nginx" "${_arg_nginx_conf_d_dir}" 'stream_*.conf'
}

###########################################################################################
# Prepares the named volumes used by the postgres image
#
# Globals:
#   _arg_chown_postgres
#   _arg_config_dir
#   _arg_secrets_dir
#   _arg_ssl_dir
#   _arg_postgres_initdb_d_dir
#   _arg_postgres_etc_postgresql_dir
#   _arg_postgres_var_certs_dir
#   _arg_enable_postgres_ssl
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

prepare_postgres_volumes() {
  set_permissions --dir-chmod "0700" --chown "${_arg_chown_postgres}" \
    "${_arg_postgres_etc_postgresql_dir}"

  set_permissions --dir-chmod "0755" --chown "${_arg_chown_postgres}" \
    "${_arg_postgres_initdb_d_dir}"

  file_copy --chmod "0600" --chown "${_arg_chown_postgres}" \
    "${_arg_secrets_dir}/postgres-passwd.env" \
    "${_arg_postgres_etc_postgresql_dir}/postgres-passwd"

  file_copy --chmod "0755" --chown "${_arg_chown_postgres}" \
    "${_arg_config_dir}/db/init-db.sh" "${_arg_postgres_initdb_d_dir}/init-db.sh"

  if [[ "${_arg_enable_postgres_ssl}" == "on" ]]; then
    file_copy --chmod "0644" --chown "${_arg_chown_postgres}" \
      "${_arg_ssl_dir}/db/server.crt" "${_arg_postgres_var_certs_dir}/server.crt"

    file_copy --chmod "0600" --chown "${_arg_chown_postgres}" \
      "${_arg_ssl_dir}/db/server.key" "${_arg_postgres_var_certs_dir}/server.key"
  fi
}

###########################################################################################
# Prepares the named volumes used by the minio image
#
# Globals:
#   _arg_chown_minio
#   _arg_ssl_dir
#   _arg_minio_certs_dir
#   _arg_minio_data_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

prepare_minio_volumes() {
  set_permissions --dir-chmod "0700" --chown "${_arg_chown_minio}" \
    "${_arg_minio_data_dir}"

  set_permissions --dir-chmod "0755" --chown "${_arg_chown_minio}" \
    "${_arg_minio_certs_dir}"

  create_dir "${_arg_minio_certs_dir}/CAs" "0022"

  copy_extra_ca_certificates --chmod "0644" --chown "${_arg_chown_minio}" \
    --ca-directory "${_arg_ssl_dir}/ca-certificates" \
    --output "${_arg_minio_certs_dir}/CAs"
}

###########################################################################################
# Prepares the named volumes used by the mlflow-tracking image
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

prepare_mlflow_volumes() {
  return 0
}

###########################################################################################
# Prepares the named volumes used by the dbadmin image
#
# Globals:
#   _arg_chown_dbadmin
#   _arg_nginx_etc_ssl_dir
#   _arg_dbadmin_certs_dir
#   _arg_dbadmin_data_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

prepare_dbadmin_volumes() {
  set_permissions --dir-chmod "0700" --chown "${_arg_chown_dbadmin}" \
    "${_arg_dbadmin_data_dir}"

  set_permissions --dir-chmod "0755" --chown "${_arg_chown_dbadmin}" \
    "${_arg_dbadmin_certs_dir}"

  file_copy --chmod "0644" --chown "${_arg_chown_dbadmin}" \
    "${_arg_nginx_etc_ssl_dir}/certs/ca-certificates.crt" \
    "${_arg_dbadmin_certs_dir}/cacert.pem"
}

###########################################################################################
# Prepares the named volumes used by the redis image
#
# Globals:
#   _arg_chown_redis
#   _arg_redis_data_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

prepare_redis_volumes() {
  set_permissions --dir-chmod "0700" --chown "${_arg_chown_redis}" \
    "${_arg_redis_data_dir}"
}

###########################################################################################
# Prepares the named volumes used by the restapi image
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

prepare_restapi_volumes() {
  return 0
}

###########################################################################################
# Prepares the named volumes used by the mc image
#
# Globals:
#   _arg_chown_mc
#   _arg_ssl_dir
#   _arg_mc_ca_certificates_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

prepare_mc_volumes() {
  set_permissions --dir-chmod "0755" --chown "${_arg_chown_mc}" \
    "${_arg_mc_ca_certificates_dir}"

  copy_extra_ca_certificates --chmod "0644" --chown "${_arg_chown_mc}" \
    --ca-directory "${_arg_ssl_dir}/ca-certificates" \
    --output "${_arg_mc_ca_certificates_dir}"
}

###########################################################################################
# Prepare a shallow clone of the dioptra GitHub repo
#
# Globals:
#   DIOPTRA_GIT_REPO_URL
#   _arg_clone_branch
#   _arg_init_repos_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

prepare_dioptra_repo_clone() {
  git_clone --dir-chmod "0755" --file-chmod "0644" --chown "root:root" --single-branch \
    --force --branch "${_arg_clone_branch}" "${DIOPTRA_GIT_REPO_URL}" \
    "${_arg_init_repos_dir}"
}

###########################################################################################
# The top-level function in the script
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

main() {
  prepare_nginx_volumes
  prepare_postgres_volumes
  prepare_minio_volumes
  prepare_mlflow_volumes
  prepare_restapi_volumes
  prepare_redis_volumes
  prepare_dbadmin_volumes
  prepare_mc_volumes
  prepare_dioptra_repo_clone
}

###########################################################################################
# Main script
###########################################################################################

main
# ] <-- needed because of Argbash
