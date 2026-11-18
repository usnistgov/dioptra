# Public CA certificates

This folder contains public root CA certificates trusted by Dioptra's services. Do not place private keys here.

When Dioptra generates certificates, initialization saves the public CA certificate as `dioptra-local-ca.crt`. Additional CA certificates must use PEM format, with one certificate per `.crt` file.

See [Configure Certificate Trust](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/adding-certificates.html) for adding CA certificates and configuring browser or Python-client trust. If you supply your own server certificates, see [Configure SSL/TLS Certificates](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/enabling-ssl-tls.html) for selecting their CA certificates in `config/ssl.toml`.
