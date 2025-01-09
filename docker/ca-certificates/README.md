# Extra CA certificates (optional)

**IMPORTANT: These CA certificates will only be used to build the container images, they will _NOT_ be available at runtime.**

If you have extra CA certificates that you want to include in the build containers, copy them into this folder before running any of the `make build-*` commands.
Only CA certificate files that meet the following criteria will be bundled and used in the build containers:

-   Each CA certificate file must be in the PEM format.
    The PEM format encodes the certificate using base64 and stores it in a plain text file between two lines, `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----`.
-   Each file should include one, and only one, CA certificate.
    Do not bundle multiple CA certificates together.
-   Each PEM-formatted CA certificate file **must** have the file extension `crt`, for example `ca-root.crt`.
    If your CA certificate has a different file extension (such as `pem`), rename it to `crt` after copying to this folder.

## How do I know if I need to do this?

There are some common situations where it is necessary to provide one or more extra CA certificates:

1.  You are building the containers in a corporate environment that has its own certificate authority and that terminates all HTTPS traffic and then re-encrypts and re-signs it before sending it to you.
2.  You are building the containers in a corporate environment that has its own certificate authority and the containers need access to resources or repository mirrors on the corporate network.

If these situations do not apply to you, or if you are unsure if they apply to you, then it is recommended that you try to build the containers without adding anything to this folder first.
If the build process fails due to an HTTPS or SSL error, then that is a telltale sign that you need to add extra CA certificates to this folder.
