# Local Scripts for Configuring and Running a development instance of Dioptra

## Note for Windows Users

These instructions and bash scripts are for macOS/Linux/WSL2 environments only.
Running a full end-to-end job with Dioptra is **not possible natively on Windows**, as the Dioptra worker will not start.
[Windows-specific instructions for developers working on the frontend or REST API are available in the MANUAL.md file](./MANUAL.md).

## 0. Pre-Requisites and Considerations

### Install uv

If you are developing for Dioptra, you are required to use `uv` to manage your development environment.

#### Why uv?

1.  `uv` is a tool (according to [the README of the project](https://github.com/astral-sh/uv) in GitHub) meant to replace `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`, `twine`, `virtualenv`, and more.
2.  `uv` is implemented predominantly in Rust, which makes it **much faster** than most of the python-native tools
3.  `uv` is backwards compatible with pip-style interfaces
4.  `uv` is installable either by `curl` or `pip`
5.  `uv` works on **Linux, MacOS, and Windows**
6.  `uv` can install and manage **Python versions** similar to PyEnv
7.  `uv` generates a cross-platform `uv.lock` lock-file

#### Installing uv

Install `uv` using the official standalone installer:

    curl -LsSf https://astral.sh/uv/install.sh | sh

#### Verifying uv Install

The simplest way to verify successful installation of `uv`:

    # Obtain version of the UV installed
    uv -V
    # or
    uv --version

`uv` also can provide the list of commands and options, when ran without parameters:

    # Display commands and options available for use in UV
    uv

`uv` also can report python and tools configuration directories:

    # Location of the UV-installed Python Versions
    uv python dir

    # Location of the UV-installed tools
    uv tool dir

### Clone the Dioptra code repository

Before continuing, you must clone the git repository to your machine:

    # SSH-based cloning
    git clone git@github.com:usnistgov/dioptra.git ~/dioptra/dev

    # HTTPS-based cloning
    git clone https://github.com/usnistgov/dioptra.git ~/dioptra/dev

## 1. Set-up DIOPTRA environment in your terminal

<a name="step1"></a>
The configuration may be set-up through the use of a configuration file or directly on the command-line.

### a. Configuration File <a name="config-file"></a>

Below is an example of a configuration file. This example can be saved into the root of the project directory (e.g. as `env-dev.cfg`).

```conf

### Env Variable for GitHub Branch
DIOPTRA_GIT_BRANCH=dev

### Deployment Path location; stores files created during runs
DIOPTRA_DEPLOY_DIR=~/di/di-dep

### The source code location
DIOPTRA_CODE_DIR=~/di/di-src

### [OPTIONAL-ENTRY] Environment Info
### Auto-Generated from ENV, if not explicitly provided
DIOPTRA_CONFIG_INFO=Dev-Dioptra for Tuning Unit-Tests

### [OPTIONAL-ENTRY] Python virtual environment to use
### Auto-Generated in the form
### Provide this value if you want to use preferred or already existing name of the Python virtual environment
DIOPTRA_ENV_NAME=.env-dev
```

[Learn more about config files ...](#learn-more-config)

#### Initialize the environment

From the root directory of the project, initialize the environment using the `dev-set.sh` script and the environment flag to point to the environment file you created:

```sh
source ./dev-kb/local-setup/dev-set.sh -e ./env-dev.cfg
```

#### [Optional] Alternate script locations

The scripts and environment configurations may be copied into the parent directory of the project (one level up) or another location to make paths simpler:

```sh
source ../dev-set.sh --env ../env-dev.cfg
```

### b. Using the Command-line

The development configuration may also be provided through command-line parameters:

```sh
source ./dev-kb/local-setup/dev-set.sh -t dev -w ~/di/di-dep -s ~/di/di-src
```

[Learn more about sourcing dev-set.sh ...](#learn-more-source)

### c. [OPTIONAL] Review Environment

To review the environment run the following commands in your newly-sourced terminal:

```sh
env | sort | grep DIOPTRA
```

### d. [OPTIONAL] Review Digest

To review a digest of the environment settings use the command below.

```sh
printf "${DIOPTRA_CONFIG_DETAILS}"
```

Note: printf is used above as echo -e switch is inconsistent between shells

**The terminal where the environment was sourced using `dev-set.sh` may now be used for Dioptra development setup and utilization.**

## 2. Run set-up Script

The `setup.sh` script will setup working and source directories using the configuration from Step 1. Necessary directories will be created, repository cloned, and correct branch checked out.

  1.  Initialize a terminal environment as described in [Step 1](#step1)
  2.  Run the setup script:

  ```sh
  ./setup.sh
  ```

## 3. Start Flask

  1.  Initialize **NEW TERMINAL** environment as described in [Step 1](#step1)
  2.  Run the Flask startup script:

  ```sh
  ./run-flask.sh
  ```

## 4. Start Redis

  1.  Initialize **NEW TERMINAL** environment as described in [Step 1](#step1)
  2.  Run the Redis startup script:

  ```sh
  ./run-redis.sh
  ```

## 5. Start Worker

  1.  Initialize **NEW TERMINAL** environment as described in [Step 1](#step1)
  2.  Run the Worker startup script:

  ```sh
  ./run-worker.sh
  ```

## 6. Start Front-End

  1.  Initialize **NEW TERMINAL** environment as described in [Step 1](#step1)
  2.  Run the Front-End startup script:

  ```sh
  ./run-front.sh
  ```

## Extended Notes

### <a id="learn-more-config"></a>More on How to Compose Config Files

**Note:** The key names are **case-sensitive**.

**Note:** The configuration file currently has the following four configuration parameter names:

-   DIOPTRA_GIT_BRANCH
-   DIOPTRA_DEPLOY_DIR
-   DIOPTRA_CODE_DIR
-   DIOPTRA_CONFIG_INFO [OPTIONAL]
-   DIOPTRA_ENV_NAME [OPTIONAL]

See the [example]#a-configuration-file) above for usage. DIOPTRA_CONFIG_NAME is optional and will be composed (in case it is not provided) by the script using the mandatory keys.

**Note:** If you want to change the names of the config variables, then the script logic must be augmented to accommodate the changes. The names from within the config file are **mapped to the environment variables** and **do not directly become environment variables**. Case-insensitive configuration names are a nice-to-have feature.

### <a id="learn-more-source"></a>Additional Ways to Source Dioptra Environment Using `dev-set.sh`

#### Parameter names also can be used in the mid-/full-word forms

```sh
source ./dev-set.sh --tag dev --work ./di-dep --source ./di-src
```

or

```sh
source ./dev-set.sh --tag dev --deploy ./di-dep  --source ./di-src
```

or

```sh
source ./dev-set.sh --tag dev --wrk ./di-dep  --src ./di-src
```

or

```sh
source ./dev-set.sh --tag dev --dep ./di-dep  --src ./di-src
```
