# Extra CA Certificates (Optional)

**These CA certificates are only used during the Docker image build. They are not available at runtime.**

Most users do not need to add anything to this folder. If you are unsure whether you need custom CA certificates, try building the images first without them. If the build fails with an HTTPS or SSL error, that is a sign you need to add certificates here.

## When you might need this

Some network environments use their own certificate authority (CA) to manage encrypted traffic. This is common in corporate or institutional networks where:

- HTTPS traffic is intercepted, decrypted, and re-encrypted by a network proxy before reaching your machine.
- Internal package repositories or container registries are signed by the organization's own CA rather than a publicly trusted one.

In these situations, the Docker build process cannot verify HTTPS connections to download packages unless you provide the organization's CA certificate.

## How to add certificates

1. Obtain the CA certificate file(s) from your network administrator.
2. Copy each certificate into this folder.
3. Each file must meet these requirements:
   - **PEM format**: The file contents are base64-encoded text between `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----` lines.
   - **One certificate per file**: Do not bundle multiple certificates into a single file.
   - **`.crt` file extension**: If your certificate file has a different extension (such as `.pem`), rename it to `.crt`.
4. Build the Docker images as usual with `make build-all` (or any of the `make build-*` commands).
