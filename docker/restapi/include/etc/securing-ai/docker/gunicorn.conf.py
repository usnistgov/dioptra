# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
chdir = "/work"
bind = "0.0.0.0:5000"
proc_name = "securingai"

# configure workers
workers = 7
max_requests = 1000
timeout = 60
graceful_timeout = 60
keepalive = 10
