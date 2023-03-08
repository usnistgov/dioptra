# Extra CA certificates (optional)

**IMPORTANT: This folder is for CA certificates, not your server's public certificate(s) and private key(s).**

If you have extra CA certificates that you want to include in the containers at runtime, copy them into this folder before running the `init-deployment.sh` script.
Only CA certificate files that meet the following criteria will be bundled and made available to the containers at runtime:

-   Each CA certificate file must be in the PEM format.
    The PEM format encodes the certificate using base64 and stores it in a plain text file between two lines, `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----`.
-   Each file should include one, and only one, CA certificate.
    Do not bundle multiple CA certificates together.
-   Each PEM-formatted CA certificate file **must** have the file extension `crt`, for example `ca-root.crt`.
    If your CA certificate has a different file extension (such as `pem`), rename it to `crt` after copying to this folder.

## How do I know if I need to do this?

There are some common situations where it is necessary to provide one or more extra CA certificates:

1.  You are running the containers in a corporate environment that has its own certificate authority and that terminates all HTTPS traffic and then re-encrypts and re-signs it before sending it to you.
2.  You are running the containers in a corporate environment that has its own certificate authority and the containers need to access resources on the corporate network.
3.  You are using one or more self-signed certificates to encrypt communications between the containers.

If none of these situations apply to you, or if you are unsure if they apply to you, then it is recommended that you run `init-deployment.sh` and try starting the deployment without adding anything to this folder first.
If the `init-deployment.sh` script or one of the deployed containers logs an HTTPS or SSL error, then that is a telltale sign that you might need to add extra CA certificates to this folder.
