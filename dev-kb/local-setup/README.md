# Local Scripts for Configuring and Running a development instance of Dioptra 

## 0. Pre-Requisites and Considerations:
- **[Important]** The current version of Python required to run Dioptra is 3.11.4 or higher
- _[Optional]_ If you use `pyenv` [recommended] to manage python versions in your development environment:
  - Ensure that the `versions` subcommand includes 3.11.4 or higher by running:
    ```sh
    pyenv versions
    ```
    - The following example output shows that Python `3.11.10` is already installed and available.
    ```
      system
      3.11.0
      3.11.2
      3.11.10 
    ```
  - To work with the scripts, use PyEnv to set up a local version for the directory you plan to use Dioptra in with the following command:
    ```sh
    pyenv local 3.11.10
    ```

  - N.B.: Check `pyenv local --help` to understand precedence order used by pyenv

## 1. Set-up DIOPTRA environment in your terminal
<a name="step1"></a>
The configuration may be set-up through the use of a configuration file or directly on the command-line.

### a. Configuration File <a name="config-file"></a>

Below is an example of a configuration file. This example can be saved into the root of the project directory (e.g. as ```env-dev.cfg```).

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
From the root directory of the project, initialize the environment using the ```dev-set.sh``` script and the environment flag to point to the environment file you created: 
```sh
source ./dev-kb/local-setup/dev-set.sh -e ./env-dev.cfg
```

#### [Optional] Alternate script locations
The scripts and environment configurations may be copied into the parent directory of the project (one level up) or another location to make paths simpler:
```sh
source ../dev-set.sh --env ../env-dev.cfg
```

### b. Using the Command-line:
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
  1. Initialize a terminal environment as described in [Step 1](#step1)
  2. Run the setup script:
  ```sh
  ./setup.sh
  ```

## 3. Start Flask
  1. Initialize **NEW TERMINAL** environment as described in [Step 1](#step1)
  2. Run the Flask startup script:
  ```sh
  ./run-flask.sh
  ```

## 4. Start Redis
  1. Initialize **NEW TERMINAL** environment as described in [Step 1](#step1)
  2. Run the Redis startup script:
  ```sh
  ./run-redis.sh
  ```

## 5. Start Worker
  1. Initialize **NEW TERMINAL** environment as described in [Step 1](#step1)
  2. Run the Worker startup script:
  ```sh
  ./run-worker.sh
  ```

## 6. Start Front-End
  1. Initialize **NEW TERMINAL** environment as described in [Step 1](#step1)
  2. Run the Front-End startup script:
  ```sh
  ./run-front.sh
  ```


## Extended Notes

### <a id="learn-more-config"></a>More on How to Compose Config Files:

**Note:** The key names are **case-sensitive**.

**Note:** The configuration file currently has the following four configuration parameter names:
- DIOPTRA_GIT_BRANCH
- DIOPTRA_DEPLOY_DIR
- DIOPTRA_CODE_DIR
- DIOPTRA_CONFIG_INFO [OPTIONAL]
- DIOPTRA_ENV_NAME [OPTIONAL]

See the [example]#a-configuration-file) above for usage. DIOPTRA_CONFIG_NAME is optional and will be composed (in case it is not provided) by the script using the mandatory keys. 

**Note:** If you want to change the names of the config variables, then the script logic must be augmented to accommodate the changes. The names from within the config file are **mapped to the environment variables** and **do not directly become environment variables**. Case-insensitive configuration names are a nice-to-have feature.

### <a id="learn-more-source"></a>Additional Ways to Source Dioptra Environment Using `dev-set.sh`:

#### Parameter names also can be used in the mid-/full-word forms:
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
