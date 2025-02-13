# Local Scripts for Development DIOPTRA Running

1. ## Set up DIOPTRA
   1. #### [Optional] Compose the environment config-file. Save the file (e.g. as ```my-env1.cfg```) File examples:

    ```
    ### Env Variable for GitHub Branch 
    DIOPTRA_BRANCH=dev
    ### Env Variable for Deployment Path
    DIOPTRA_DEPLOY=~/di/di-dep
    ### Env Variable for Source Path
    DIOPTRA_CODE=~/di/di-src
    ```

    #### Use of alternative names may make the variables intent more clear, e.g.:

    ```
    git_branch=dev
    dir_work=~/dio/dio2-wrk
    dir_source=~/dio/dio2-src
    ```

    #### The key names are case-insensitive, but locked set. E.g., branch names are restricted to any capitalization of the ```DIOPTRA_BRANCH``` or ```GIT_BRANCH```. So, use of ```Git_branch``` or ```git_branch``` is OK, but ```git_stash``` would fail proper initialization (unless the script logic is augmented).

   2. #### Initialize the environment using the ```dev-env+.sh``` script and environment flag pointing to the file you had created:

    ```
    source ./dev-env+.sh -e ./my-env1.cfg
    ```
    ##### or in the mid- or full-word forms:
    ```
    source ./dev-env+.sh --env ./my-env1.cfg

    ```
    ```
    source ./dev-env+.sh --environment ./my-env1.cfg

    ```

    #### Or ALTERNATIVELY you can source environment variables directly:

    ##### in the shorthand form:
    ```
    source ./dev-env+.sh -t dev -d ./dio/dio-wrkS1 -s ./dio/dio-srcS1

    ```

    ##### or in the mid- or full-word forms:
    ```
    source ./dev-env+.sh --tag dev --wrk ~/dio/dio-wrkM1 --src ~/dio/dio-srcM1

    ```

    ```
    source ./dev-env+.sh --tag dev --work ./dio/dio-wrkF2 --source ./dio/dio-srcF2

    ```

   3. #### In the shell environment sourced in the steps 1 and 2 or only 2, run the setup script:
    ```
    ./stup.sh
    ```


2. ## Start Flask
   1. ### Source-initialize environment as described in steps 1.i and 1.ii or only 1.ii
   2. ### In the initialized environment run Flask startup script
   ```
   ./run-flask.sh
   ```

3. ## Start Redis
   1. ### Source-initialize environment as described in steps 1.i and 1.ii or only 1.ii
   2. ### In the initialized environment run REdis startup script
   ```
   ./run-redis.sh
   ```

4. ## Start Worker
   1. ### Source-initialize environment as described in steps 1.i and 1.ii or only 1.ii
   2. ### In the initialized environment run Worker startup script
   ```
   ./run-worker.sh
   ```
