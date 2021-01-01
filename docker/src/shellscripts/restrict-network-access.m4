#!/bin/bash

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_OPTIONAL_REPEATED([cidr],[c],[CIDR to whitelist],[])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Restrict network access at runtime\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly cidr_list="${_arg_cidr[@]}"
readonly logname="Restrict Network Access"

###########################################################################################
# Allow all traffic on the loopback interface
#
# Globals:
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

allow_loopback_connections() {
  echo "${logname}: update firewall rules to permit traffic on loopback interface"

  sudo /sbin/iptables -I INPUT 1 -i lo -j ACCEPT -m comment --comment "Loopback interface"
  sudo /sbin/iptables -I OUTPUT 1 -o lo -j ACCEPT -m comment --comment "Loopback interface"
}

###########################################################################################
# Whitelist traffic
#
# Globals:
#   cidr_list
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

allow_cidr_connections() {
  for cidr in ${cidr_list[@]}; do
    echo "${logname}: update firewall rules to permit traffic on CIDR '${cidr}'"

    sudo /sbin/iptables -A INPUT -s ${cidr} -j ACCEPT
    sudo /sbin/iptables -A OUTPUT -d ${cidr} -j ACCEPT
  done
}

###########################################################################################
# Drop all traffic by default
#
# Globals:
#   logname
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

drop_all_other_connections() {
  echo "${logname}: update firewall rules to drop all other traffic by default"

  sudo /sbin/iptables -A INPUT -j DROP
  sudo /sbin/iptables -A OUTPUT -j DROP
}

###########################################################################################
# Main script
###########################################################################################

allow_loopback_connections
allow_cidr_connections
drop_all_other_connections
# ] <-- needed because of Argbash
