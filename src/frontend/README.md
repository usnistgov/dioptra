# dioptra

This template should help get you started developing with Vue 3 in Vite.

## Prerequisites

In order for this web app to work properly, the REST API also needs to be served. After creating a Python virtual environment ([see README.md here](../../README.md)) but before starting the server, if you haven't already, run a database migration to add the latest table definitions to a local SQLite database that will be stored in the project root,

```sh
DIOPTRA_RESTAPI_DEV_DATABASE_URI=sqlite:///$(pwd)/dioptra-dev.db DIOPTRA_RESTAPI_ENV=dev flask db upgrade -d src/migrations
```

Next, run the Flask server in development mode,

```sh
DIOPTRA_RESTAPI_DEV_DATABASE_URI=sqlite:///$(pwd)/dioptra-dev.db DIOPTRA_RESTAPI_ENV=dev flask run --host ::1
```

From here, move on to starting the vite development server using the instructions below.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur) + [TypeScript Vue Plugin (Volar)](https://marketplace.visualstudio.com/items?itemName=Vue.vscode-typescript-vue-plugin).

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

### Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```
