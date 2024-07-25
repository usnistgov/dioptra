# frontend

This template should help get you started developing with Vue 3 in Vite.

## Prerequisites

In order to get a development instance of the web app to work properly, the REST API also needs to be served.

The following steps will be necessary:

-   Create a [Python virtual environment](../../README.md#setting-up-the-python-virtual-environment) and use `pip-sync` to install the development packages

-   Follow the [User Setup](../../README.md#user-setup) instructions

    -   Be sure to activate the virtual environment you created in the previous step

    -   Install the other prerequisites needed to use the cookiecutter template

    -   Use the cookiecutter template to generate the scripts, configuration files, and Docker Compose files you will need for your development environment

    -   Build the containers

-   Run a database migration to add the latest table definitions to a local SQLite database that will be stored in the project root using the following commands if using bash shell:

    ```sh
    export DIOPTRA_RESTAPI_DEV_DATABASE_URI=sqlite:///$(pwd)/dioptra-dev.db
    export DIOPTRA_RESTAPI_ENV=dev
    export DIOPTRA_SESSION_PROTECTION=none
    dioptra-db autoupgrade
    ```

-   If running windows powershell, use these commands instead:

    ```
    $env:DIOPTRA_RESTAPI_DEV_DATABASE_URI="sqlite:///$pwd\dioptra-dev.db"
    $env:DIOPTRA_RESTAPI_ENV="dev"
    $env:DIOPTRA_SESSION_PROTECTION="none"
    dioptra-db autoupgrade
    ```

-   Several modifications to the files produced from the cookiecutter template will be necessary

    -   First modify the `init-deployments.sh` so that the `main` function at the bottom of the file has been commented out:

        ```sh
        main() {
          parse_args "${@}"
          init_scripts
          # init_extra_ca_certificates
          init_named_volumes
          init_minio
          # start_db_service
          # manage_postgres_ssl
          stop_services
        }
        ```

    -   Modify the `docker-compose.yml`

        -   Comment out all of the services except for `dioptra-deployment-redis` and `dioptra-deployment-minio` (the `volumes` section at the bottom can be left unmodified)

            -   Add the following `ports` section to `dioptra-deployment-minio` service:

                ```yaml
                    ports:
                      - 127.0.0.1:9000:9000/tcp
                      - 127.0.0.1:9001:9001/tcp
                ```

            -   Add the following `ports` section to `dioptra-deployment-redis` service:

                ```yaml
                    ports:
                      - 127.0.0.1:6379:6379/tcp
                ```

-   Run the `init-deployments.sh` script

-   Now create a new script file outside of the source code directory, `start-flask`, to start-up the flask server in development mode.

    -   `chmod 755 start-flask` to make it executable

    -   Environment variables from the `secrets/dioptra-deployment-restapi.env` file should be added

    -   Environment variables from `envs/dioptra-deployment-restapi.env` should be copied

        -   for `DIOPTRA_RESTAPI_ENV` change from `prod` to `dev`

        -   Change the hostname for each of the URLs to `localhost` from their generated values

    -   The final script file should look something like the below:

        ```sh
        export AWS_ACCESS_KEY_ID=dioptra-restapi
        export AWS_SECRET_ACCESS_KEY=<generated secret>
        export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
        export MLFLOW_TRACKING_URI=http://localhost:5000
        export RQ_REDIS_URI=redis://localhost:6379/0
        export DIOPTRA_RESTAPI_DEV_DATABASE_URI=sqlite:///$(pwd)/dioptra-dev.db
        export DIOPTRA_RESTAPI_ENV=dev
        flask run --host ::1
        ```

-   Prior to running `start-flask` you will need to run `docker-compose up -d` in the cookie cutter template directory to start some required services

    -   Checking that everything started normally can be done through `docker-compose logs -f`

    -   Shutting down the services can be done through `docker-compose down`

-   When running the `start-flask` script as configured above you will need to run it the current directory as the project directory where the SQLite database was initialized.

From here, move on to starting the vite development server using the instructions below.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur) + [TypeScript Vue Plugin (Volar)](https://marketplace.visualstudio.com/items?itemName=Vue.vscode-typescript-vue-plugin).

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [TypeScript Vue Plugin (Volar)](https://marketplace.visualstudio.com/items?itemName=Vue.vscode-typescript-vue-plugin) to make the TypeScript language service aware of `.vue` types.

If the standalone TypeScript plugin doesn't feel fast enough to you, Volar has also implemented a [Take Over Mode](https://github.com/johnsoncodehk/volar/discussions/471#discussioncomment-1361669) that is more performant. You can enable it by the following steps:

1. Disable the built-in TypeScript Extension
    1) Run `Extensions: Show Built-in Extensions` from VSCode's command palette
    2) Find `TypeScript and JavaScript Language Features`, right click and select `Disable (Workspace)`
2. Reload the VSCode window by running `Developer: Reload Window` from the command palette.

## Customize configuration

See [Vite Configuration Reference](https://vitejs.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```
