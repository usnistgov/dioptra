# Postgres server certificates

To configure Postgres to encrypt database connections, copy the appropriate server certificate and private key into this folder before running the `init-deployment.sh` script with the `--enable-postgres-ssl` option flag.
The initialization script expects the following file names:

-   **Server certificate:** `server.crt`
-   **Private key:** `server.key`

If your server certificate has been signed using an intermediate certificate, then it should be concatenated with the appropriate bundle of chained certificates provided to you by the signing certificate authority.
**When concatenating, make sure that the server certificate comes _before_ the chained certificates:**

```sh
cat server-certificate.crt bundle.crt > server.crt
```

Note that some certificate authorities may provide an option to download the bundled version, or even distribute the bundled version by default.
