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

# Certificate installation can be interrupted between volume writes. Refuse a
# partially installed set before a managed service starts, even when every input
# certificate came from an external issuer. Recheck current validity as well as
# recorded bytes: unchanged certificates can expire after installation.
set -euo pipefail

COMPLETION_CHECKSUMS="/etc/ssl/dioptra-complete.sha256"
COMPLETION_MARKER="/etc/ssl/dioptra-complete.json"

###########################################################################################
# Print a certificate-installation error to stderr and stop startup.
#
# Globals:
#   None
# Arguments:
#   Error message, a string
# Returns:
#   Exits 1.
###########################################################################################

fail() {
  echo "${1}" >&2
  exit 1
}

###########################################################################################
# Require the recorded file type, hard-link count, permissions and ownership.
#
# Globals:
#   None
# Arguments:
#   File path, a string
#   Expected stat output in type:links:mode:uid:gid format, a string
# Returns:
#   Exits nonzero when validation fails.
###########################################################################################

require_file_metadata() {
  local path="${1}" expected="${2}"

  if [[ "$(stat -c '%F:%h:%a:%u:%g' "${path}")" != "${expected}" ]]; then
    fail "Unsafe or missing TLS installation file: ${path}; use manage_ssl.py recover."
  fi
}

###########################################################################################
# Check server certificate validity, chain and every recorded DNS or IP identity.
#
# Globals:
#   None
# Arguments:
#   Certificate-chain path, a string (empty for a trust-only consumer)
#   Validation trust-file path, a string
#   Completion checksum record path, a string
# Returns:
#   Exits nonzero when validation fails.
###########################################################################################

check_serving_certificate() {
  local certificate="${1}" trust="${2}" checks="${3}"
  local identities=0 prefix kind value

  if [[ -z "${certificate}" ]]; then
    return
  fi
  case "${certificate}:${trust}" in
  /etc/ssl/server.crt:/etc/ssl/dioptra-server-trust.crt | /etc/dioptra/tls/server.crt:/etc/dioptra/tls/dioptra-server-trust.crt) ;;
  *) fail 'Invalid TLS serving paths in completion record.' ;;
  esac
  if [[ "${certificate}" == /etc/dioptra/tls/server.crt ]]; then
    if [[ "$(stat -c '%F:%a:%u:%g' /etc/dioptra/tls)" != "directory:700:$(id -u):$(id -g)" ]]; then
      fail 'Unsafe API TLS directory; expected a real mode-0700 directory owned by the serving account.'
    fi
  fi
  while read -r prefix kind value; do
    [[ "${prefix}" == '#' ]] || continue
    case "${kind}" in
    dns) openssl verify -purpose sslserver -CAfile "${trust}" -untrusted "${certificate}" -verify_hostname "${value}" "${certificate}" ;;
    ip) openssl verify -purpose sslserver -CAfile "${trust}" -untrusted "${certificate}" -verify_ip "${value}" "${certificate}" ;;
    *) continue ;;
    esac
    identities=$((identities + 1))
  done <"${checks}"
  if [[ "${identities}" -eq 0 ]]; then
    fail 'TLS serving record has no identity checks.'
  fi
}

###########################################################################################
# Require startup environment and nginx configuration to match installed policy.
#
# Globals:
#   DIOPTRA_TLS_ALLOWED_AUTHORITIES
#   DIOPTRA_TLS_KEY_EXCHANGE
#   DIOPTRA_PUBLIC_HOST
#   DIOPTRA_PUBLIC_HTTPS_PORT
# Arguments:
#   Number of transport-policy members in the checksum record, an integer
#   Server certificate path, a string (empty for a trust-only consumer)
# Returns:
#   Exits nonzero when validation fails.
###########################################################################################

check_transport_policy() {
  local policy_member="${1}" certificate="${2}"
  local environment_members=0 name expected_value actual_value config

  if [[ -n "${certificate}${DIOPTRA_TLS_ALLOWED_AUTHORITIES:-}" && "${policy_member}" -ne 1 ]]; then
    fail 'Incomplete TLS transport policy; use manage_ssl.py recover.'
  fi
  if [[ "${policy_member}" -ne 1 ]]; then
    return
  fi

  # The checksum-bound policy is public data. Read known fields; never source it.
  while IFS='=' read -r name expected_value; do
    case "${name}" in
    DIOPTRA_TLS_ALLOWED_AUTHORITIES) actual_value="${DIOPTRA_TLS_ALLOWED_AUTHORITIES:-}" ;;
    DIOPTRA_TLS_KEY_EXCHANGE) actual_value="${DIOPTRA_TLS_KEY_EXCHANGE:-}" ;;
    DIOPTRA_PUBLIC_HOST) actual_value="${DIOPTRA_PUBLIC_HOST:-}" ;;
    DIOPTRA_PUBLIC_HTTPS_PORT) actual_value="${DIOPTRA_PUBLIC_HTTPS_PORT:-}" ;;
    NGINX_CONFIG_SHA256)
      config=/etc/nginx/conf.d/https_restapi.conf
      require_file_metadata "${config}" "regular file:1:644:$(id -u):$(id -g)"
      actual_value=$(sha256sum "${config}")
      actual_value=${actual_value%% *}
      if [[ "${actual_value}" != "${expected_value}" ]]; then
        fail 'Nginx transport policy is incomplete; use manage_ssl.py recover.'
      fi
      continue
      ;;
    *) fail 'Unexpected TLS transport policy member.' ;;
    esac
    if [[ "${actual_value}" != "${expected_value}" ]]; then
      fail "TLS environment differs from the completed policy: ${name}; use manage_ssl.py recover."
    fi
    environment_members=$((environment_members + 1))
  done </etc/ssl/dioptra-transport.env
  if [[ "${environment_members}" -ne 4 ]]; then
    fail 'Incomplete TLS environment policy.'
  fi
}

###########################################################################################
# Check the complete installed file set before checking certificates and policy.
#
# Globals:
#   None
# Arguments:
#   Completion checksum record path, a string
# Returns:
#   Exits nonzero when validation fails.
###########################################################################################

check_installed_set() {
  local checks="${1}"
  local members=0 marker_member=0 policy_member=0 expected=0
  local certificate="" trust="" digest path required prefix kind value

  if ! head -n 1 "${checks}" | grep -Eq '^# generation [0-9a-f]{32}$'; then
    fail 'Invalid TLS generation identifier; use manage_ssl.py recover.'
  fi
  while read -r digest path; do
    [[ "${digest}" != '#' ]] || continue
    case "${path}" in
    /etc/ssl/dioptra-transport.env)
      required='regular file:1:644:0:0'
      policy_member=$((policy_member + 1))
      ;;
    /etc/ssl/dioptra-complete.json)
      required='regular file:1:644:0:0'
      marker_member=$((marker_member + 1))
      ;;
    /etc/ssl/server.key | /etc/dioptra/tls/server.key) required="regular file:1:600:$(id -u):$(id -g)" ;;
    /etc/ssl/server.crt | /etc/dioptra/tls/server.crt) required="regular file:1:644:$(id -u):$(id -g)" ;;
    /etc/ssl/dioptra-server-trust.crt | /etc/dioptra/tls/dioptra-server-trust.crt | /etc/ssl/certs/ca-certificates.crt | /usr/local/share/ca-certificates/dioptra-*.crt) required='regular file:1:644:0:0' ;;
    *) fail "Unexpected TLS member: ${path}" ;;
    esac
    require_file_metadata "${path}" "${required}"
    members=$((members + 1))
  done <"${checks}"
  while read -r prefix kind value; do
    [[ "${prefix}" == '#' ]] || continue
    case "${kind}" in
    count) expected="${value}" ;;
    certificate) certificate="${value}" ;;
    trust) trust="${value}" ;;
    esac
  done <"${checks}"
  case "${expected}" in
  '' | *[!0-9]*) fail 'Invalid TLS member count.' ;;
  esac
  if [[ "${members}" -eq 0 || "${members}" -ne "${expected}" || "${marker_member}" -ne 1 ]]; then
    fail 'Incomplete TLS checksum record; use manage_ssl.py recover.'
  fi
  if ! sha256sum --check --strict --status "${checks}"; then
    fail 'TLS generation contents differ from the completion record; use manage_ssl.py recover.'
  fi
  check_serving_certificate "${certificate}" "${trust}" "${checks}"
  check_transport_policy "${policy_member}" "${certificate}"
}

###########################################################################################
# Refuse incomplete, altered or expired certificate installations before startup.
#
# Globals:
#   DIOPTRA_SSL_MANAGED
#   COMPLETION_CHECKSUMS
#   COMPLETION_MARKER
# Arguments:
#   None
# Returns:
#   Exits nonzero when validation fails.
###########################################################################################

main() {
  if [[ "${DIOPTRA_SSL_MANAGED:-0}" != "1" ]]; then
    return
  fi
  require_file_metadata "${COMPLETION_CHECKSUMS}" 'regular file:1:644:0:0'
  require_file_metadata "${COMPLETION_MARKER}" 'regular file:1:644:0:0'
  check_installed_set "${COMPLETION_CHECKSUMS}"
}

main "${@}"
