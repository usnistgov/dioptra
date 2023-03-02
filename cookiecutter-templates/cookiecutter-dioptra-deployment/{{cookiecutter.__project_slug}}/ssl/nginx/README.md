# NGINX server certificates

To configure NGINX to run a HTTPS server, copy the appropriate server certificate and private key into this folder before running the `init-deployment.sh` script with the `--enable-nginx-ssl` option flag.
The initialization script expects the following file names:

-   **Server certificate:** `server.crt`
-   **Private key:** `server.key`

If your server certificate has been signed using an intermediate certificate, then it should be concatenated with the appropriate bundle of chained certificates provided to you by the signing certificate authority.
**When concatenating, make sure that the server certificate comes _before_ the chained certificates:**

```sh
cat server-certificate.crt bundle.crt > server.crt
```

Note that some certificate authorities may provide an option to download the bundled version, or even distribute the bundled version by default.

In addition to copying in the server certificate and private key files, you also need to edit the NGINX service's published ports and health check test in the `docker-compose.yml` file.
Open `docker-compose.yml` in a text editor, find the `{{ cookiecutter.__project_slug }}-nginx:` block, and edit the ports and health check test to match the YAML snippet below.

```yaml
dioptra-deployment-nginx:
  healthcheck:
    test:
      [
        "CMD",
        "/usr/local/bin/healthcheck.sh",
        "http://localhost:30080",
        # "http://localhost:35000",
        # "http://localhost:35050/login",
        # "http://localhost:39000",
        # "http://localhost:39001",
        "https://localhost:30443",
        "https://localhost:35000",
        "https://localhost:35050/login",
        "https://localhost:39000",
        "https://localhost:39001",
      ]
  ports:
    - {{ "127.0.0.1:" if cookiecutter.nginx_expose_ports_on_localhost_only.lower() == "true" else "" }}80:30080/tcp
    - {{ "127.0.0.1:" if cookiecutter.nginx_expose_ports_on_localhost_only.lower() == "true" else "" }}443:30443/tcp
    - {{ "127.0.0.1:" if cookiecutter.nginx_expose_ports_on_localhost_only.lower() == "true" else "" }}35432:5432/tcp
    - {{ "127.0.0.1:" if cookiecutter.nginx_expose_ports_on_localhost_only.lower() == "true" else "" }}35000:35000/tcp
    - {{ "127.0.0.1:" if cookiecutter.nginx_expose_ports_on_localhost_only.lower() == "true" else "" }}35050:35050/tcp
    - {{ "127.0.0.1:" if cookiecutter.nginx_expose_ports_on_localhost_only.lower() == "true" else "" }}39000:39000/tcp
    - {{ "127.0.0.1:" if cookiecutter.nginx_expose_ports_on_localhost_only.lower() == "true" else "" }}39001:39001/tcp
```
