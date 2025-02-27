# Local Scripts for Development DIOPTRA Running

  

### 1. Set up DIOPTRA environment in yor terminal

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

  
##### **Note:** The key names are **case-insensitive**, but constitute a script hard-coded and locked set. E.g., branch name key values are not restricted to any particular capitalization of the ```DIOPTRA_GIT_BRANCH``` or ```Dioptra_Git_Branch```. 

##### **Note:** Script is currently locked to these 4 names: DIOPTRA_CONFIG_NAME, DIOPTRA_GIT_BRANCH, DIOPTRA_DEPLOY_DIR, DIOPTRA_CODE_DIR. See the example above for usage. DIOPTRA_CONFIG_NAME is optional and will be composed (in case it was not provided) by script with the reasonable environment description that can be deduced from the mandatory keys. 

##### **Note:** If you want to change the names of the config variables, then the script logic must be augmented to accommodate the changes. The names from within the config file are **mapped to the environment variables** and **do not directly become environment variables**. So, having the names case-insensitive is just a nice-to-have feature for better readability.

#### b. From the top-level of the project source code initialize the environment using the ```dev-set.sh``` script and environment flag pointing to the environment file you had created:
 

```sh
source ./dev-kb/local-setup/dev-set.sh -e ./dev-kb/local-setup/dev-env.sh/my-env1.cfg
```

##### or as some developers may prefer: copy the scripts and environment configurations into the parent directory (one level up) to make paths simpler:

```sh
source ../dev-set.sh --env ../my-env1.cfg
```


#### Or ALTERNATIVELY you can source environment variables with direct parameters-to-environment mapping:

##### in the shorthand form:

```sh
source ../dev-set.sh -t dev -w ./dio/dio-wrk-V1 -s ./dio/dio-src-V1 
```

  

##### or in the mid-/full-word forms:

```sh
source ./dev-set.sh --tag dev --work ./dio/dio-wrkF2 --source ./dio/dio-srcF2

or 

source ./dev-set.sh --tag dev --deploy ./dio/dio-wrkF2 --source ./dio/dio-srcF2

or 

source ./dev-set.sh --tag dev --wrk ./dio/dio-wrkF2 --src ./dio/dio-srcF2

or 

source ./dev-set.sh --tag dev --dep ./dio/dio-wrkF2 --src ./dio/dio-srcF2

```

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
./stup.sh
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