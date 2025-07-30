# Manual Instructions

The following are a set of manual instructions to set-up a local development environment.
The instructions for the automated scripts can be found in [README.md](README.md).

## Local Development setup (without containers)

### Clone Repository
- Clone the repository at https://github.com/usnistgov/dioptra:
  ```
  git clone git@github.com:usnistgov/dioptra.git ~/dioptra/dev
  ```
  or
  ```
  git clone https://github.com/usnistgov/dioptra.git ~/dioptra/dev
  ```
- `cd ~dioptra/dev`
- `git checkout dev`
- [Install redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/)
- Create a work directory for files `mkdir -p ~/dioptra/deployments/dev`

### Setting up the Python virtual environment
The following assumes you are in the root of the cloned repository as completed in the
prior section.

Developers must use Python 3.11 and create a virtual environment using one of the requirements.txt files in the `requirements/` directory in order to make contributions to this project.
Ensure that you have Python 3.11 installed and that it is available in your PATH, and then identify the requirements file that you want to use:

| Filename | OS | Architecture | Tensorflow | PyTorch |
| :--- | :---: | :---: | :--- | :--- |
| linux-amd64-py3.11-requirements-dev.txt | Linux | x86-64 | ❌ | ❌ |
| linux-amd64-py3.11-requirements-dev-tensorflow.txt | Linux | x86-64 | ✅ | ❌ |
| linux-amd64-py3.11-requirements-dev-pytorch.txt | Linux | x86-64 | ❌ | ✅ |
| linux-arm64-py3.11-requirements-dev.txt | Linux | arm64 | ❌ | ❌ |
| linux-arm64-py3.11-requirements-dev-tensorflow.txt | Linux | arm64 | ✅ | ❌ |
| linux-arm64-py3.11-requirements-dev-pytorch.txt | Linux | arm64 | ❌ | ✅ |
| macos-amd64-py3.11-requirements-dev.txt | macOS | x86-64 | ❌ | ❌ |
| macos-amd64-py3.11-requirements-dev-tensorflow.txt | macOS | x86-64 | ✅ | ❌ |
| macos-amd64-py3.11-requirements-dev-pytorch.txt | macOS | x86-64 | ❌ | ✅ |
| macos-arm64-py3.11-requirements-dev.txt | macOS | arm64 | ❌ | ❌ |
| macos-arm64-py3.11-requirements-dev-tensorflow.txt | macOS | arm64 | ✅ | ❌ |
| macos-arm64-py3.11-requirements-dev-pytorch.txt | macOS | arm64 | ❌ | ✅ |
| win-amd64-py3.11-requirements-dev.txt | Windows | x86-64 | ❌ | ❌ |
| win-amd64-py3.11-requirements-dev-tensorflow.txt | Windows | x86-64 | ✅ | ❌ |
| win-amd64-py3.11-requirements-dev-pytorch.txt | Windows | x86-64 | ❌ | ✅ |

Next, use the `venv` module to create a new virtual environment:

```sh
python -m venv .venv
```

Activate the virtual environment after creating it.
To activate it on macOS/Linux:

```sh
source .venv/bin/activate
```

To activate it on Windows:

```powershell
.venv\Scripts\activate
```

Next, upgrade `pip` and install `pip-tools`:

```sh
python -m pip install --upgrade pip pip-tools
```

Finally, use `pip-sync` to install the dependencies in your chosen requirements file and install `dioptra` in development mode.
On macOS/Linux:

```sh
# Replace "linux-amd64-py3.11-requirements-dev.txt" with your chosen file
pip-sync requirements/linux-amd64-py3.11-requirements-dev.txt
```

On Windows:

```powershell
# Replace "win-amd64-py3.11-requirements-dev.txt" with your chosen file
pip-sync requirements\win-amd64-py3.11-requirements-dev.txt
```

If the requirements file you used is updated, or if you want to switch to another requirements file (you need access to the Tensorflow library, for example), just run `pip-sync` again using the appropriate filename.
It will install, upgrade, and uninstall all packages accordingly and ensure that you have a consistent environment.


- [Create a python virtual environment](#setting-up-the-python-virtual-environment)

- The following describes commands to execute in four different terminal windows:
  1. Flask Terminal
     - Environment variables that must be set for flask:
       ```
       DIOPTRA_RESTAPI_DEV_DATABASE_URI="sqlite:////home/<username>/dioptra/deployments/dev/dioptra-dev.db"  
       DIOPTRA_RESTAPI_ENV=dev  
       DIOPTRA_RESTAPI_VERSION=v1
       MLFLOW_TRACKING_URI="http://localhost:35000"
       ```
       N.B.: replace <username> with your username. On some systems the home path may also be different. Verify the expansion of '~' with the `pwd` command while in the appropriate directory.

       The example above uses the sqlite connection string.
       [PostgreSQL](https://www.postgresql.org/docs/current/index.html) can also be used
       and would look something like (but should use values appropriate for your
       configuration see [PostgreSQL Connection URIs](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING-URIS) for documentation.):

       ```
       postgresql://dioptra:somepassword@localhost:5432/restapi
       ```

     - Activate the python environment set-up in prior steps
     - `dioptra-db autoupgrade`
     - `flask run`

  2. Frontend UI Terminal
     - Commands to get a Frontend running:
       ```bash
       cd src/fronted
       npm install
       npm run dev
       ```

  3. Redis Terminal
     - `redis-server`

  4. Dioptra Worker
     - Starting a Dioptra Worker requires the following environment variables:
       ```
       DIOPTRA_WORKER_USERNAME="dioptra-worker"  # This must be a registered user in the Dioptra app
       DIOPTRA_WORKER_PASSWORD="password"        # Must match the username's password
       DIOPTRA_API="http://localhost:5000"       # This is the default API location when you run `flask run`
       RQ_REDIS_URI="redis://localhost:6379/0"   # This is the default URI when you run `redis-server`
       MLFLOW_S3_ENDPOINT_URL="http://localhost:35000"  # If you're running a MLflow Tracking server, update this to point at it. Otherwise, this is a placeholder.
       MLFLOW_TRACKING_URI="http://localhost:35000"
       OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES   # Macs only, needed to make the RQ worker (i.e. the Dioptra Worker) work
       ```
     - Activate the python environment set-up in prior steps (e.g. `source .venv/bin/activate`)
     - With the prior environment variables set then execute the following commands:
       ```bash
       mkdir -p ~/dioptra/deployments/dev/workdir/
       cd ~/dioptra/deployments/dev/workdir/
       dioptra-worker-v1 'Tensorflow CPU'  # Assumes 'Tensorflow CPU' is a registered Queue name
       ```
- Frontend app is available by default at http://localhost:5173 (the frontend terminal windows should also indicate the URL to use)
- Create Dioptra worker in the Frontend UI or through API. curl command for interacting with API (assuming you have the environment variables in Step iv set) is:
  ```
  curl http://localhost:5000/api/v1/users/ -X POST --data-raw "{\"username\": \"$DIOPTRA_WORKER_USERNAME\",  \"email\": \"dioptra-worker@localhost\", \"password\": \"$DIOPTRA_WORKER_PASSWORD\", \"confirmPassword\": \"$DIOPTRA_WORKER_PASSWORD\"}"
  ```
- Create 'Tensorflow CPU' Queue -- this needs to agree with the queue name used in Step iv.