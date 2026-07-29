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
# ARG_OPTIONAL_SINGLE([username],[],[The system username for the Postgres instance],[postgres])
# ARG_OPTIONAL_SINGLE([dbname],[],[The system database for the Postgres instance],[postgres])
# ARG_OPTIONAL_BOOLEAN([set-ssl-filepaths],[],[Set the filepaths of the SSL certificate and key files for the Postgres instance])
# ARG_OPTIONAL_BOOLEAN([ssl],[],[Enable ssl for the Postgres instance])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Utility for enabling and disabling SSL in Postgres.\n])
# ARGBASH_GO()

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail ${DEBUG:+-x}

###########################################################################################
# Global parameters
###########################################################################################

LOGNAME="Enable Postgres SSL"
POSTGRES_CERTS_DIR="/var/lib/postgresql/certs"
POSTGRES_DATA_DIR="/var/lib/postgresql/data"
POSTGRES_PG_GBA_CONF_FILE="${POSTGRES_DATA_DIR}/pg_hba.conf"
POSTGRES_SSL_CERT_FILE="${POSTGRES_CERTS_DIR}/server.crt"
POSTGRES_SSL_KEY_FILE="${POSTGRES_CERTS_DIR}/server.key"

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
# Set the filepaths of the SSL certificate and key files
#
# Globals:
#   POSTGRES_SSL_CERT_FILE
#   POSTGRES_SSL_KEY_FILE
#   _arg_dbname
#   _arg_set_ssl_filepaths
#   _arg_username
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

__set_ssl_filepaths() {
  psql -v ON_ERROR_STOP=1 --username "${_arg_username}" --dbname "${_arg_dbname}" <<-EOSQL
		ALTER SYSTEM SET ssl_cert_file TO '${POSTGRES_SSL_CERT_FILE}';
		ALTER SYSTEM SET ssl_key_file TO '${POSTGRES_SSL_KEY_FILE}';
	EOSQL
}

set_ssl_filepaths() {
  if [[ "${_arg_set_ssl_filepaths}" == "off" ]]; then
    return 0
  fi

  log_info "Setting the filepaths of the SSL certificate and key files on the Postgres" \
    "instance"

  if ! __set_ssl_filepaths; then
    log_error "Running of SQL command to set the filepaths of the SSL certificate and" \
      "key files failed, exiting..."
    exit 1
  fi
}

###########################################################################################
# Enable SSL on the Postgres instance
#
# Globals:
#   POSTGRES_PG_GBA_CONF_FILE
#   _arg_dbname
#   _arg_username
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

__enable_ssl() {
  psql -v ON_ERROR_STOP=1 --username "${_arg_username}" --dbname "${_arg_dbname}" <<-EOSQL
		ALTER SYSTEM SET ssl TO 'ON';
	EOSQL
}

__enforce_ssl_connections() {
  cat <<-EOPGHBA > "${POSTGRES_PG_GBA_CONF_FILE}"
		# TYPE  DATABASE        USER            ADDRESS                 METHOD
		# "local" is for Unix domain socket connections only
		local   all             all                                     trust
		# IPv4 local connections:
		host    all             all             127.0.0.1/32            trust
		# IPv6 local connections:
		host    all             all             ::1/128                 trust
		# Allow replication connections from localhost, by a user with the
		# replication privilege.
		local   replication     all                                     trust
		host    replication     all             127.0.0.1/32            trust
		host    replication     all             ::1/128                 trust
		# Enforce SSL when connecting from another service as the dioptra user
		hostssl mlflow-tracking dioptra         all                     scram-sha-256
		hostssl restapi         dioptra         all                     scram-sha-256
	EOPGHBA
}

enable_ssl() {
  log_info "Enabling SSL on the Postgres instance"

  if ! __enable_ssl; then
    log_error "Running of SQL command failed, exiting..."
    exit 1
  fi

  log_info "Updating ${POSTGRES_PG_GBA_CONF_FILE} to require SSL connections to the" \
    "Postgres instance"

  if ! __enforce_ssl_connections; then
    log_error "Updating of ${POSTGRES_PG_GBA_CONF_FILE} failed, exiting..."
    exit 1
  fi
}

###########################################################################################
# Disable SSL on the Postgres instance
#
# Globals:
#   POSTGRES_PG_GBA_CONF_FILE
#   _arg_dbname
#   _arg_username
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

__disable_ssl() {
  psql -v ON_ERROR_STOP=1 --username "${_arg_username}" --dbname "${_arg_dbname}" <<-EOSQL
		ALTER SYSTEM SET ssl TO 'OFF';
	EOSQL
}

__allow_unencrypted_connections() {
  cat <<-EOPGHBA > "${POSTGRES_PG_GBA_CONF_FILE}"
		# TYPE  DATABASE        USER            ADDRESS                 METHOD
		# "local" is for Unix domain socket connections only
		local   all             all                                     trust
		# IPv4 local connections:
		host    all             all             127.0.0.1/32            trust
		# IPv6 local connections:
		host    all             all             ::1/128                 trust
		# Allow replication connections from localhost, by a user with the
		# replication privilege.
		local   replication     all                                     trust
		host    replication     all             127.0.0.1/32            trust
		host    replication     all             ::1/128                 trust
		# Allow unencrypted connections from another service as the dioptra user
		host    mlflow-tracking dioptra         all                     scram-sha-256
		host    restapi         dioptra         all                     scram-sha-256
	EOPGHBA
}

disable_ssl() {
  log_info "Disabling SSL on the Postgres instance"

  if ! __disable_ssl; then
    log_error "Running of SQL command failed, exiting..."
    exit 1
  fi

  log_info "Updating ${POSTGRES_PG_GBA_CONF_FILE} to allow unencrypted connections to" \
    "the Postgres instance"

  if ! __allow_unencrypted_connections; then
    log_error "Updating of ${POSTGRES_PG_GBA_CONF_FILE} failed, exiting..."
    exit 1
  fi
}

###########################################################################################
# Route option for enabling/disabling SSL on the Postgres instance
#
# Globals:
#   _arg_ssl
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

route_ssl_option() {
  if [[ "${_arg_ssl}" == "on" ]]; then
    enable_ssl
  else
    disable_ssl
  fi
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
  set_ssl_filepaths
  route_ssl_option
}

###########################################################################################
# Main script
###########################################################################################

main
# ] <-- needed because of Argbash
