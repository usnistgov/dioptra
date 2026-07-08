# Developer Guide

If you have not already, please review [CONTRIBUTING.md](CONTRIBUTING.md) for more complete information on expectations for contributions.

<!-- markdownlint-disable MD007 MD030 -->
- [Note for Windows Users](#note-for-windows-users)
- [Developer Set-up](#developer-set-up)
    - [Building the documentation](#building-the-documentation)
    - [Lint and format your files](#lint-and-format-your-files)
    - [Type check your files](#type-check-your-files)
    - [Checking your commit message with gitlint](#checking-your-commit-message-with-gitlint)
    - [Running unit tests with pytest](#running-unit-tests-with-pytest)
    - [Cleanup](#cleanup)
    - [Upgrading the uv.lock file](#upgrading-the-uvlock-file)
<!-- markdownlint-enable MD007 MD030 -->

## Note for Windows Users

Please note that **only a subset of Dioptra's components work natively on Windows**.
You can develop for the frontend or REST API natively on Windows, and [Windows-specific instructions for setting up the environment are available in the dev-kb/local-setup/MANUAL.md file](dev-kb/local-setup/MANUAL.md).
However, if you need to run all of Dioptra's components locally, you must [install and use WSL2](https://learn.microsoft.com/en-us/windows/wsl/install).

## Developer Set-up

See the [Local Developer Set-up](dev-kb/local-setup/README.md) knowledge base article for instructions.

### Building the documentation

This project uses Sphinx to generate the documentation published at <https://pages.nist.gov/dioptra> and uses [tox](https://tox.wiki/en/stable/) to run it.
If you haven't done so yet, install `tox` as a uv tool:

    uv tool install --python 3.11 tox --with tox-uv

To build the documentation locally, run:

    uvx tox run -e web-compile,docs

### Lint and format your files

This project uses [ruff](https://docs.astral.sh/ruff) to lint and format code and uses [tox](https://tox.wiki/en/stable/) to run it.
If you haven't done so yet, install `tox` as a uv tool:

    uv tool install --python 3.11 tox --with tox-uv

To run the code linter, use:

    # Run this to lint (but not fix) your code
    uvx tox run -e lint

    # Run this to lint your code and fix it where possible (includes import sorting)
    uvx tox run -e lint -- --fix src/dioptra

To run the code formatter, use:

    # Run this to check (but not fix) your code formatting
    uvx tox run -e format

    # Run this to fix your code formatting automatically
    uvx tox run -e format -- src/dioptra

At a minimum, you should run this before opening a merge request on your branch:

    uvx tox run -e lint -- --select I --fix src/dioptra
    uvx tox run -e format -- src/dioptra

If commiting any frontend changes, run the following from the `src/frontend` directory to lint and format frontend code:

    npm run lint
    npm run format

### Type check your files

This project uses [mypy](https://mypy.readthedocs.io/en/stable/) to type check code and uses [tox](https://tox.wiki/en/stable/) to run it.
If you haven't done so yet, install `tox` as a uv tool:

    uv tool install --python 3.11 tox --with tox-uv

To run the type checker, use:

    uvx tox run -e mypy

### Checking your commit message with gitlint

This project has a [commit style guide](./COMMIT_STYLE_GUIDE.md) that is enforced using the `gitlint` tool and uses [tox](https://tox.wiki/en/stable/) to run it.
If you haven't done so yet, install `tox` as a uv tool:

    uv tool install --python 3.11 tox --with tox-uv

Developers are expected to run `gitlint` and validate their commit message before opening a Pull Request.
After committing your contribution, run:

    uvx tox run -e gitlint

### Running unit tests with pytest

This project stores its pytest-based unit tests in the `tests/` folder and uses [tox](https://tox.wiki/en/stable/) to run it.
If you haven't done so yet, install `tox` as a uv tool:

    uv tool install --python 3.11 tox --with tox-uv

Developers are expected to create new unit tests to validate any new features or behavior that they contribute and to verify that all unit tests pass before opening a Pull Request.
To run the unit tests:

    uvx tox run -e pytest -- tests/unit
    uvx tox run -e pytest-cookiecutter
    uvx tox run -e pytest-extra

### Running frontend end-to-end tests with Playwright

This project stores Playwright tests in the `src/frontend/tests` folder.  To run them, please do the following:

1. Ensure your [frontend dev server](https://github.com/usnistgov/dioptra/blob/main/dev-kb/local-setup/README.md#6-start-front-end) is running.
If you haven't installed the frontend packages, in `src/frontend` run `npm install` to make sure Playwright is installed.

2. Ensure your dev mode Flask server is stopped.  The test script starts its own backend using a test database.

3. If your [env-dev.cfg](https://github.com/usnistgov/dioptra/blob/main/dev-kb/local-setup/README.md#a-configuration-file-) is not in your project root or the directory above it, please specify it's location location using this command

        export DIOPTRA_E2E_ENV_FILE=/path/to/env-dev.cfg

4. To run the tests, execute the following from `src/frontend`

        npm run test:e2e:with-backend

### Cleanup

> **NOTE:** This command will not work in a Windows environment.

Run the following to clear away the project's temporary files, which includes the sentinel dotfiles that are created in `build/` when using `make`:

    make clean

### Upgrading the uv.lock file

The uv.lock file is generated by uv as a standardized lockfile that specifies exact versions of Python dependencies, ensuring reproducible and consistent builds across different environments.
To keep dependencies up-to-date and apply important fixes or improvements, a maintainer should periodically upgrade the lockfile by running:

    uv lock --upgrade
