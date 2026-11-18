# NGINX server certificates

Initialization creates nginx's certificate and private key in this folder by default. Certificate settings are in `config/ssl.toml`.

To use your own certificates, follow [Configure SSL/TLS Certificates](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/enabling-ssl-tls.html) before initialization. This folder uses these filenames:

- `server.crt` contains the PEM server certificate followed by any required intermediate certificates.
- `server.key` contains the matching private key.

Keep the private key protected and out of version control. To replace certificates in an existing deployment, follow [Replace Deployment Certificates](https://pages.nist.gov/dioptra/how-to/setup-dioptra/replace-deployment-certificates.html).
