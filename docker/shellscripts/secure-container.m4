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
# Script adapted from the work https://github.com/jupyter/docker-stacks/blob/56e54a7320c3b002b8b136ba288784d3d2f4a937/base-notebook/start.sh.
# See copyright below.
#
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# Neither the name of the Jupyter Development Team nor the names of its
# contributors may be used to endorse or promote products derived from this
# software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_OPTIONAL_SINGLE([default-username],[],[Non-root username used during runtime],[dioptra])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Secure Docker container at runtime\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly chown_extra="${CHOWN_EXTRA-}"
readonly chown_home="${CHOWN_HOME-}"
readonly chown_home_opts="${CHOWN_HOME_OPTS-}"
readonly default_username="${_arg_default_username}"
readonly dioptra_user="${DIOPTRA_USER}"
readonly dioptra_gid="${DIOPTRA_GID}"
readonly dioptra_group="${DIOPTRA_GROUP-}"
readonly dioptra_uid="${DIOPTRA_UID}"
readonly logname="Secure Container"

###########################################################################################
# Change username from default (if it exists)
#
# Globals:
#   default_username
#   dioptra_user
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

change_username() {
  local username_check_exit_code=$(
    id "${default_username}" &>/dev/null
    echo $?
  )

  if [[ ${username_check_exit_code} == 0 && ${dioptra_user} != ${default_username} ]]; then
    echo "${logname}: set username to ${dioptra_user}"
    usermod -d "/home/${dioptra_user}" -l "${dioptra_user}" ${default_username}
  fi
}

###########################################################################################
# Fix permissions for provisioned storage, such as for NFS mounts
#
# Globals:
#   chown_extra
#   chown_home
#   chown_home_opts
#   dioptra_gid
#   dioptra_uid
#   dioptra_user
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

fix_storage_permissions() {
  if [[ ${chown_home} == 1 || ${chown_home} == yes ]]; then
    echo "${logname}: changing ownership of /home/${dioptra_user} to ${dioptra_uid}:${dioptra_gid} with options '${chown_home_opts}'"
    chown ${chown_home_opts} ${dioptra_uid}:${dioptra_gid} /home/${dioptra_user}
  fi

  if [[ ! -z ${chown_extra} ]]; then
    for extra_dir in $(echo ${chown_extra} | tr ',' ' '); do
      echo "${logname}: changing ownership of ${extra_dir} to ${dioptra_uid}:${dioptra_gid} with options '${chown_extra_OPTS}'"
      chown ${chown_extra_OPTS} ${dioptra_uid}:${dioptra_gid} ${extra_dir}
    done
  fi
}

###########################################################################################
# Update home and working directories if the username changed
#
# Globals:
#   default_username
#   dioptra_user
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

update_user_dirs() {
  if [[ "${dioptra_user}" != "${default_username}" ]]; then
    if [[ ! -e "/home/${dioptra_user}" ]]; then
      echo "${logname}: relocating home dir to /home/${dioptra_user}"
      mv "/home/${default_username}" "/home/${dioptra_user}" ||
        ln -s "/home/${default_username}" "/home/${dioptra_user}"
    fi

    if [[ "${PWD}/" == "/home/${default_username}/"* ]]; then
      local newcwd="/home/${dioptra_user}/${PWD:13}"
      echo "${logname}: setting CWD to ${newcwd}"
      cd "${newcwd}"
    fi
  fi
}

###########################################################################################
# Change UID:GID of dioptra_user to dioptra_uid:dioptra_gid if it does not match
#
# Globals:
#   default_username
#   dioptra_gid
#   dioptra_group
#   dioptra_uid
#   dioptra_user
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

update_user_uid_gid() {
  if [[ "${dioptra_uid}" != $(id -u ${dioptra_user}) || "${dioptra_gid}" != $(id -g ${dioptra_user}) ]]; then
    echo "${logname}: set user ${dioptra_user} UID:GID to: ${dioptra_uid}:${dioptra_gid}"

    if [[ "${dioptra_gid}" != $(id -g ${dioptra_user}) ]]; then
      groupadd -g ${dioptra_gid} -o ${dioptra_group:-${dioptra_user}}
    fi

    userdel ${dioptra_user}
    useradd --home /home/${dioptra_user} -u ${dioptra_uid} -g ${dioptra_gid} -G 100 -l ${dioptra_user}
  fi
}

###########################################################################################
# Disable sudo permissions for non-root user
#
# Globals:
#   default_username
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

disable_sudo_permissions() {
  if [[ -f /etc/sudoers.d/dioptra_user ]]; then
    echo "${logname}: removing sudo permissions for ${default_username}"
    sudo /bin/rm -f /etc/sudoers.d/dioptra_user
  fi
}

###########################################################################################
# Ensure runtime user has an entry in passwd file
#
# Globals:
#   default_username
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

ensure_runtime_user_in_passwd() {
  local status=0 && whoami &>/dev/null || local status=$? && true
  local default_username_reverse=$(echo ${default_username} | rev)

  if [[ "${status}" != "0" ]]; then
    if [[ -w /etc/passwd ]]; then
      echo "${logname}: adding passwd file entry for $(id -u)"

      cat /etc/passwd | sed -e \"s/^${default_username}:/${default_username_reverse}:/\" >/tmp/passwd
      echo \"${default_username}:x:$(id -u):$(id -g):,,,:/home/${default_username}:/bin/bash\" >>/tmp/passwd
      cat /tmp/passwd >/etc/passwd
      rm /tmp/passwd
    else
      echo "${logname}: Container must be run with group \"root\" to update passwd file"
    fi
  fi
}

###########################################################################################
# Warn if the user isn't going to be able to write files to home directory
#
# Globals:
#   default_username
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

warn_if_home_read_only() {
  if [[ ! -w /home/${default_username} ]]; then
    echo "${logname}: container must be run with group \"users\" to update files"
  fi
}

###########################################################################################
# Warn if uid/gid cannot be overriden.
#
# Globals:
#   dioptra_gid
#   dioptra_uid
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

warn_if_no_override_uid_gid() {
  if [[ ! -z "${dioptra_uid}" && "${dioptra_uid}" != "$(id -u)" ]]; then
    echo "${logname}: container must be run as root to set \$DIOPTRA_UID"
  fi

  if [[ ! -z "${dioptra_gid}" && "${dioptra_gid}" != "$(id -g)" ]]; then
    echo "${logname}: container must be run as root to set \$DIOPTRA_GID"
  fi
}

###########################################################################################
# Secure the container at runtime
#
# Globals:
#   default_username
#   dioptra_gid
#   dioptra_uid
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

secure_container() {
  if [[ "$(id -u)" == 0 ]]; then
    change_username
    fix_storage_permissions
    update_user_dirs
    update_user_uid_gid
  else
    if [[ \
      "${dioptra_uid}" == "$(id -u ${default_username})" && \
      "${dioptra_gid}" == "$(id -g ${default_username})" ]]; then
      ensure_runtime_user_in_passwd
      warn_if_home_read_only
    else
      warn_if_no_override_uid_gid
    fi
  fi

  disable_sudo_permissions
}

###########################################################################################
# Execute script
###########################################################################################

secure_container
# ] <-- needed because of Argbash
