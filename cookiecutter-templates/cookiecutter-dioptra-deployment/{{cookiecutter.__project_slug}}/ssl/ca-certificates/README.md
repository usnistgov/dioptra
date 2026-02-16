# Extra CA Certificates (Optional)

**This folder is for CA certificates only, not server certificates or private keys.** For server certificates, see the [ssl/db/](../db/) and [ssl/nginx/](../nginx/) folders.

**These CA certificates are bundled and made available to the deployment containers at runtime.**

Most users do not need to add anything to this folder. If you are unsure whether you need custom CA certificates, try starting the deployment without them first. If the `init-deployment.sh` script or one of the running containers logs an HTTPS or SSL error, that is a sign you need to add certificates here.

## When you might need this

Some network environments use their own certificate authority (CA) to manage encrypted traffic. This is common in corporate or institutional networks where:

- HTTPS traffic is intercepted, decrypted, and re-encrypted by a network proxy before reaching your machine.
- Internal resources that the containers need to access are signed by the organization's own CA rather than a publicly trusted one.
- Self-signed certificates are used to encrypt communications between the containers themselves.

In these situations, the containers cannot verify HTTPS connections unless you provide the appropriate CA certificate.

## How to add certificates

1. Obtain the CA certificate file(s) from your network administrator.
2. Copy each certificate into this folder.
3. Each file must meet these requirements:
   - **PEM format**: The file contents are base64-encoded text between `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----` lines.
   - **One certificate per file**: Do not bundle multiple certificates into a single file.
   - **`.crt` file extension**: If your certificate file has a different extension (such as `.pem`), rename it to `.crt`.
4. Run `./init-deployment.sh` to bundle the certificates and make them available to the containers.
