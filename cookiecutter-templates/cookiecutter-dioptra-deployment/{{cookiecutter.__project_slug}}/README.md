# {{ cookiecutter.deployment_name }}

A collection of scripts, configuration files, and Docker Compose files for initializing and deploying Dioptra on a single host machine.

## Quick start

Dioptra generates the required certificates during initialization. To use your own certificates, follow [Configure SSL/TLS Certificates](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/enabling-ssl-tls.html) before initializing the deployment.

Open a terminal and run the following to initialize and start Dioptra.

```sh
cd {{ cookiecutter.__project_slug }}

# Initialize the deployment
# Replace "main" with the branch that matches your container images if different
./init-deployment.sh --branch main

# Start Dioptra
{{ cookiecutter.docker_compose_path }} up -d
```

See [Initialization Script Reference](https://pages.nist.gov/dioptra/how-to/setup-dioptra/reference/init-deployment-script-reference.html) for initialization options and behavior.

Use a fresh deployment when adopting this configuration and remove the retired `DIOPTRA_DEPLOY_SECRET_KEY` setting. Initialization does not convert previous deployment state.

Open the HTTPS address reported by initialization. If your browser does not trust the deployment CA, follow [Configure Certificate Trust](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/adding-certificates.html#how-to-trust-public-issuer) before logging in.

Keep a protected backup of the certificate files and configuration listed in [Certificate Backups](https://pages.nist.gov/dioptra/how-to/setup-dioptra/reference/deployment-folder-reference.html#reference-deployment-certificate-backups).

To stop Dioptra:

```sh
{{ cookiecutter.docker_compose_path }} down
```

## What's in this folder

| File / Directory                       | Purpose                                                                   |
| -------------------------------------- | ------------------------------------------------------------------------- |
| `config/`                              | Service and certificate configuration files                      |
| `envs/`                                | Environment variable files for each Dioptra service                       |
| `scripts/`                             | Deployment initialization scripts and `manage_ssl.py` for certificate maintenance            |
| `secrets/`                             | Generated secret files (passwords) -- do not commit to git                |
| `.ssl-private/`                        | Generated CA, certificate installation records, and recovery files        |
| `ssl/`                                 | CA certificates and server certificate/key pairs for SSL/TLS              |
| `systemd/`                             | Generated systemd service file for Linux deployments                      |
| `docker-compose.yml`                   | Main Compose file defining all Dioptra services                           |
| `docker-compose.override.yml.template` | Starting point for custom Compose overrides                               |
| `docker-compose.init.yml`              | Compose file used by `init-deployment.sh` during initialization           |
| `init-deployment.sh`                   | Deployment initialization script                                          |
| `.env`                                 | Generated environment file with service passwords -- do not commit to git |

## Documentation

For detailed instructions, see the Dioptra documentation:

- [Prepare Your Deployment](https://pages.nist.gov/dioptra/how-to/setup-dioptra/prepare-deployment.html) (initial setup guide)
- [Update Your Deployment](https://pages.nist.gov/dioptra/how-to/setup-dioptra/update-deployment.html) (fetching template updates with cruft)
- [Deployment Commands Reference](https://pages.nist.gov/dioptra/how-to/setup-dioptra/reference/deployment-commands-reference.html) (start, stop, restart, logs)
- [Deployment Folder Reference](https://pages.nist.gov/dioptra/how-to/setup-dioptra/reference/deployment-folder-reference.html) (detailed file descriptions)
- [Initialization Script Reference](https://pages.nist.gov/dioptra/how-to/setup-dioptra/reference/init-deployment-script-reference.html) (command-line options)
- [Deployment Template Reference](https://pages.nist.gov/dioptra/how-to/setup-dioptra/reference/deployment-template-reference.html) (template variables)

**Certificate maintenance:**

- [Replace Deployment Certificates](https://pages.nist.gov/dioptra/how-to/setup-dioptra/replace-deployment-certificates.html)
- [Replace the Deployment Certificate Authority](https://pages.nist.gov/dioptra/how-to/setup-dioptra/replace-deployment-ca.html)
- [Recover an Interrupted Certificate Operation](https://pages.nist.gov/dioptra/how-to/setup-dioptra/recover-certificate-operation.html)

**Optional customizations:**

- [Docker Compose Overrides](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/using-docker-compose-overrides.html)
- [Mount Data Volumes](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/data-mounts.html)
- [GPU-Enabled Workers](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/gpu-enabled-workers.html)
- [Configure Certificate Trust](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/adding-certificates.html)
- [Configure SSL/TLS Certificates](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/enabling-ssl-tls.html)
- [Create a Custom Worker Container](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/creating-custom-workers.html)
- [Integrate Custom Containers](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/integrating-custom-containers.html)
