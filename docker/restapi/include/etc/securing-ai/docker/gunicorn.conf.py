chdir = "/work"
bind = "0.0.0.0:5000"
proc_name = "securingai"

# configure workers
workers = 7
max_requests = 1000
timeout = 60
graceful_timeout = 60
keepalive = 10
