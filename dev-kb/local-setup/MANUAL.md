# Manual Instructions

The following are a set of manual instructions to set-up a local development environment.
The instructions for the automated scripts can be found in [README.md](README.md).

<!-- markdownlint-disable MD007 MD030 -->
- [Note for Windows Users](#note-for-windows-users)
- [Environment setup](#environment-setup)
- [Limited frontend and REST API setup for Windows (no containers)](#limited-frontend-and-rest-api-setup-for-windows-no-containers)
- [Full local development setup (no containers)](#full-local-development-setup-no-containers)
<!-- markdownlint-enable MD007 MD030 -->

## Note for Windows Users

These instructions provide separate commands for Windows and macOS/Linux/WSL2.
However, please note that **only a subset of Dioptra's components work natively on Windows**.
The Windows-specific instructions are intended for developers working on the frontend or REST API, which typically do not require running the Dioptra worker.
If you need to develop or test plugins and entrypoints, running a full end-to-end job with Dioptra is **not possible natively on Windows**, as the Dioptra worker will not start.
In this case, you must [install and use WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) to perform this type of development on a Windows machine.

## Environment setup

Install `uv` using the official standalone installer:

    # macOS / Linux / WSL2
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Windows
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    # Windows (if you already have WinGet installed)
    winget install --id=astral-sh.uv  -e

For binary-installable packages, visit [the releases page in github](https://github.com/astral-sh/uv/releases) for `uv`'s latest packages and pick the package for your specific operating system and hardware combination.

Next, if you haven't already, clone the repository at <https://github.com/usnistgov/dioptra> to your machine:

    # macOS / Linux / WSL2
    # SSH-based cloning
    git clone git@github.com:usnistgov/dioptra.git ~/dioptra/dev

    # HTTPS-based cloning
    git clone https://github.com/usnistgov/dioptra.git ~/dioptra/dev

    # Windows
    # SSH-based cloning
    git clone git@github.com:usnistgov/dioptra.git $env:UserProfile\dioptra\dev

    # HTTPS-based cloning
    git clone https://github.com/usnistgov/dioptra.git $env:UserProfile\dioptra\dev

Next, use `uv` to set up your project's Python virtual environment.
Run the following command from the root of the dioptra code folder that you cloned:

> **NOTE:** To run jobs that use PyTorch-based plugins, swap `--extra tensorflow-cpu` with `--extra pytorch-cpu`. If you have a GPU available, then swap these for their GPU variants `--extra tensorflow-gpu` and `--extra pytorch-gpu`. You can only use one of these at a time.

    # macOS / Linux / WSL2
    uv sync --extra worker --extra tensorflow-cpu

    # Windows (omits the worker-specific extras)
    uv sync

Next, activate the virtual environment you created:

    # macOS / Linux / WSL2
    source .venv/bin/activate

    # Windows
    .venv\Scripts\activate

It's also recommended that you install `tox` as a uv tool:

    uv tool install --python 3.11 tox --with tox-uv

## Limited frontend and REST API setup for Windows (no containers)

> **NOTE:** The following instructions are for developers with Windows machines that are working on the frontend or REST API only

-   Clone the repository as described in [Environment setup](#environment-setup) if you haven't already
-   `cd $env:UserProfile\dioptra\dev`
-   `git checkout dev`
-   [Create a python virtual environment](#environment-setup)
-   Re-sync the installed packages using `uv`:

        # NOTE: The --extra options are not needed when developing for the frontend and REST API
        uv sync

-   The following describes commands to execute in two different terminal windows:
    1.  Flask Terminal (as written, this puts the SQLite database at `$env:UserProfile\dioptra\dev\dioptra-dev.db`)
        -   Environment variables that must be set for flask:

                $env:DIOPTRA_RESTAPI_DEV_DATABASE_URI="sqlite:///<path-to-cloned-dioptra-directory>/dioptra/dev/dioptra-dev.db"
                $env:DIOPTRA_RESTAPI_ENV=dev

            N.B.: replace `<path-to-cloned-dioptra-directory>` with the full path to the folder where you cloned Dioptra. If you followed the suggested instructions, this will be the folder pointed at by `$env:UserProfile`. The URI should use forward slashes `/` and include the drive, for example `C:/Users/username/dioptra/dev/dioptra-dev.db`.
        -   [Activate the virtual environment if you haven't already](#environment-setup)
        -   `dioptra-db autoupgrade`
        -   `flask run`

    2.  Frontend UI Terminal
        -   Commands to get a Frontend running:

                cd src\fronted
                npm install
                npm run dev

## Full local development setup (no containers)

> **NOTE:** The following instructions are for macOS / Linux / WSL2 only, it is not possible to natively run a full setup on Windows.

-   Clone the repository as described in [Environment setup](#environment-setup) if you haven't already
-   `cd ~/dioptra/dev`
-   `git checkout dev`
-   [Install redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/)
-   [Create a python virtual environment](#environment-setup)
-   Re-sync the installed packages using `uv`:

        # Replace tensorflow-cpu with tensorflow-gpu, pytorch-cpu, pytorch-gpu as needed
        uv sync --extra worker --extra tensorflow-cpu

-   The following describes commands to execute in four different terminal windows:
    1.  Flask Terminal (as written, this puts the SQLite database at `~/dioptra/dev/dioptra-dev.db`)
        -   Environment variables that must be set for flask:

                DIOPTRA_RESTAPI_DEV_DATABASE_URI="sqlite:////home/<username>/dioptra/dev/dioptra-dev.db"
                DIOPTRA_RESTAPI_ENV=dev

            N.B.: replace <username> with your username. On some systems the home path may also be different. Verify the expansion of '~' with the `pwd` command while in the appropriate directory.

        -   Activate the python environment set-up in prior steps
        -   `dioptra-db autoupgrade`
        -   `flask run`

    2.  Frontend UI Terminal
        -   Commands to get a Frontend running:

                cd src/fronted
                npm install
                npm run dev

    3.  Redis Terminal
        -   `redis-server`

    4.  Dioptra Worker
        -   Starting a Dioptra Worker requires the following environment variables:

                DIOPTRA_WORKER_USERNAME="dioptra-worker"  # This must be a registered user in the Dioptra app
                DIOPTRA_WORKER_PASSWORD="password"        # Must match the username's password
                DIOPTRA_API="http://localhost:5000"       # This is the default API location when you run `flask run`
                RQ_REDIS_URI="redis://localhost:6379/0"   # This is the default URI when you run `redis-server`
                MLFLOW_TRACKING_URI="http://localhost:35000"     # If you're running a MLflow Tracking server, update this to point at it. Otherwise, this is a placeholder.
                MLFLOW_S3_ENDPOINT_URL="http://localhost:35000"  # If you're running a MLflow Tracking server, update this to point at it. Otherwise, this is a placeholder.
                OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES   # Macs only, needed to make the RQ worker (i.e. the Dioptra Worker) work

        -   Activate the python environment set-up in prior steps (e.g. `source .venv/bin/activate`)
        -   With the prior environment variables set then execute the following commands:

                mkdir -p ~/dioptra/deployments/dev  # Create a directory for the Dioptra worker to use
                cd ~/dioptra/deployments/dev
                dioptra-worker-v1 'Tensorflow CPU'  # Assumes 'Tensorflow CPU' is a registered Queue name

-   Frontend app is available by default at <http://localhost:5173> (the frontend terminal windows should also indicate the URL to use)
-   Create Dioptra worker in the Frontend UI or through API. curl command for interacting with API (assuming you have the environment variables in Step iv set) is:

        curl http://localhost:5000/api/v1/users/ -X POST --data-raw "{\"username\": \"$DIOPTRA_WORKER_USERNAME\",  \"email\": \"dioptra-worker@localhost\", \"password\": \"$DIOPTRA_WORKER_PASSWORD\", \"confirmPassword\": \"$DIOPTRA_WORKER_PASSWORD\"}"

-   Create 'Tensorflow CPU' Queue -- this needs to agree with the queue name used in Step iv.
