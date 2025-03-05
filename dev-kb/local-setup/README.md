# Local Scripts for Development DIOPTRA Running

### 0. Pre-Requisites and Considerations:
#### a. [Important] The current version of Python required to run Dioptra is 3.11.4 and higher
#### b. [Optional] If you use `pyenv` to manage python versions in your environment [recommended to make life simpler]:
- Make sure that the `versions` subcommand includes 3.11.4 or higher versions by running:
```sh
pyenv versions
```
- The following output would imply that for dioptra setup directory you would want to set up local version `3.11.10` of Python 
```
  system
  3.11.0
  3.11.2
  3.11.10 
```
- PyEnv allows to set up local version for the directory you plan to use dioptra in with the following command:
(The command will create .python-version at the very location where the command was ran)
```sh
pyenv local 3.11.10
```

- Also, `pyenv local --help` states the following rule:  
```txt
When you run a Python command, pyenv will look for a `.python-version'
file in the current directory and each parent directory. If no such
file is found in the tree, pyenv will use the global Python version
specified with `pyenv global'. A version specified with the
`PYENV_VERSION' environment variable takes precedence over local
and global versions.
```
#### c. Regardless of how you set your Python version at Dioptra deployment the venv virtual environment setup and environment activation should work seamlessly with traditional or PyEnv setup if PyEnv local was set up as described above.

### 1. Source DIOPTRA environment in yor terminal

#### a.  [Optional] If the desired environment config file was not yet created: Compose the environment config-file. Save the file (e.g. as ```env-dev1.cfg```) File content examples:

```sh
### Optional "Environment Info"
### Maps to an environment variable DIOPTRA_CONFIG_INFO verbatim
### If absent a digest of environment SETTINGS will be 
### generated IN  DIOPTRA_CONFIG_DETAILS
DIOPTRA_CONFIG_NAME=Dev-Dioptra for Tuning Unit-Tests

### Env Variable for GitHub Branch
DIOPTRA_GIT_BRANCH=dev

### Env Variable for Deployment Path
DIOPTRA_DEPLOY_DIR=~/di/di-dep

### Env Variable for Source Path
DIOPTRA_CODE_DIR=~/di/di-src
```
[Learn more about config files ...](#learn-more-config)

#### b. From the top-level of the project source code initialize the environment using the ```dev-set.sh``` script and environment flag pointing to the environment file you had created: 

```sh
source ./dev-kb/local-setup/dev-set.sh -e ./dev-kb/local-setup/dev-env.sh/my-env1.cfg
```
##### Some developers may prefer: copy the scripts and environment configurations into the parent directory (one level up) to make paths simpler:

```sh
source ../dev-set.sh --env ../my-env1.cfg
```

#### Or ALTERNATIVELY you can source environment variables with direct parameters-to-environment mapping:

##### in the shorthand form:

```sh
source ../dev-set.sh -t dev -w ./dio/dio-wrk-V1 -s ./dio/dio-src-V1 
```
[Learn more about sourcing dev-set.sh ...](#learn-more-source)


#### c. [Optional] To review the environment (if desired) run one of the following commands in your newly-sourced terminal: 
```sh
env | sort

or 

env | sort | grep DIOPTRA
```

#### d. [Optional] To review aggregated digest of the environment settings use the command below. The reason for using printf is the echo -e switch being inconsistent between shells.
```sh
printf "${DIOPTRA_CONFIG_DETAILS}"
```

#### Now, the environment variables in the terminal process that sourced the environment using dev-set.sh should be set for performing the automated actions for Dioptra development setup and utilization. 

### 2. [Optional] If the project was not yet setup you can setup working and source directories (from ```DIOPTRA_DEPLOY_DIR``` and ```DIOPTRA_CODE_DIR```) initialized from the repository branch (defined by ```DIOPTRA_GIT_BRANCH```) if the config file was used.
#### a. Source-initialize **NEW TERMINAL** environment as described in step 1
#### b. Run the setup script:

```sh
./setup.sh
```
  

### 3. Start Flask
#### a. Source-initialize **NEW TERMINAL** environment as described in step 1
#### b. In the initialized environment run Flask startup script

```sh
./run-flask.sh
```

  

### 4. Start Redis
#### a. Source-initialize **NEW TERMINAL** environment as described in step 1
#### b. In the initialized environment run Redis startup script

```sh
./run-redis.sh
```

  

### 5. Start Worker
#### a. Source-initialize **NEW TERMINAL** environment as described in step 1
#### b. In the initialized environment run Worker startup script

```sh
./run-worker.sh
```


### 6. <a id="learn-more-config"></a>More on How to Compose Config Files:

##### **Note:** The key names are **case-insensitive**, but constitute a script hard-coded and locked set. E.g., branch name key values are not restricted to any particular capitalization of the ```DIOPTRA_GIT_BRANCH``` or ```Dioptra_Git_Branch```. 

##### **Note:** Script is currently locked to these 4 names: DIOPTRA_CONFIG_NAME, DIOPTRA_GIT_BRANCH, DIOPTRA_DEPLOY_DIR, DIOPTRA_CODE_DIR. See the example above for usage. DIOPTRA_CONFIG_NAME is optional and will be composed (in case it was not provided) by script with the reasonable environment description that can be deduced from the mandatory keys. 

##### **Note:** If you want to change the names of the config variables, then the script logic must be augmented to accommodate the changes. The names from within the config file are **mapped to the environment variables** and **do not directly become environment variables**. So, having the names case-insensitive is just a nice-to-have feature for better readability.

### 7. <a id="learn-more-source"></a>Additional Ways to Source Dioptra Environment Using `dev-set.sh`:

##### Parameter names also can be used in the mid-/full-word forms:

```sh
source ./dev-set.sh --tag dev --work ./dio/dio-wrkF2 --source ./dio/dio-srcF2

or 

source ./dev-set.sh --tag dev --deploy ./dio/dio-wrkF2 --source ./dio/dio-srcF2

or 

source ./dev-set.sh --tag dev --wrk ./dio/dio-wrkF2 --src ./dio/dio-srcF2

or 

source ./dev-set.sh --tag dev --dep ./dio/dio-wrkF2 --src ./dio/dio-srcF2

```