# Securing AI Lab Components
## MNIST-Patch Demo.

## Summary:

This demo is a variation of the original tensorflow-mnist demo, configured to run the patch attack within the DGX workstation.
The steps follow the original guide with a few additional steps for launching patch attacks.
Please see the [changelog](#changelog) section for a summary of general code changes made to this demo from the original tensorflow mnist demo.


### Mandatory: Setting container and network names for the demo.

Please replace `<username>` entry in the following files with your own personal user name:

```
demo_*.sh
docker-compose.yml
```

Alternatively: Run `find . \( ! -regex '.*/\..*' \) -type f | xargs sed -i 's/<username>/<YOUR_USER_NAME_HERE>/g'` to
automatically set the configured files with your username. Or use an IDE to update the scripts automatically.

## The following steps follow the original demo, with a new attack script available for testing.

### Optional: Setting up compatible Conda environment.

A few of the scripts (i.e. download_data.py) will require python dependencies not found in the base environment
(python-mnist, click, etc.). If you do not have a conda environment to run such scripts you can quickly create a
compatible one using the environment.yml file:

Run:
```
conda env create --name docker_tests python=3.7 -f environment.yml
conda activate docker_tests
```
To build and launch this environment.


### Setting proper permissions

Right now, our accounts are set to restrict readability of files to user-only, which interferes with mounting and
reading of local storage volumes in docker containers. In order to correct this, we'll need to create
a bash alias to update new folder permissions.

In your home directory:

Create the  `.bash_aliases` file and enter the following line into the file:

`umask 0022`

This will set future directories and folders to be readable for all users as well as within docker containers.
To ensure the changes take effect, log out and then back into the dgx-workstation.
To fix permissions for existing directories we will use the following commands.


From this directory `examples/tensorflow-mnist-classifier`, please run the following commands:

```
find . -type d -print0 | xargs -0 chmod 755
find . -type f -print0 | xargs -0 chmod 644

mkdir s3
mkdir mlruns
chmod 777 mlruns

```

This ensures that the data, mlruns, and s3 folders all have proper permissions for access within the docker containers.
The s3 and mlruns folders are currently where the docker-compose file will bind the docker containers to.

### Next: Setting up dataset and containers.

Run the following commands, from the tutorial session:


```
make data
make services
make upload-job
```

Once you are finished run `make teardown` to close the docker container.

NOTE: If the tarball upload triggers another permissions issue (i.e. "/work/*.tar.gz is not readable")

Run: `chmod 644 workflows.tar.gz`

To set the code tarball file to 'readable' for the S3 upload.

Then re-run: `make upload-job`

### Next: Launching GPU-configured docker jobs.

Right now, due to differences in docker vs docker-compose, GPU containers have to be manually executed via `docker run`
command. To simplify this, the following bash scripts have been provided:

1. `demo_run_training.sh` - Loads, trains, and tests a lightweight model on regular MNIST dataset.
2. `demo_run_attack.sh`   - Generates adversarial patches from model produced in step 2.
3. `demo_deploy_patch.sh` - Applies patches generated in step 2 to create a custom patched-MNIST dataset. Includes test and training data.
4. `demo_test_patch_dataset.sh` - Run patched dataset through model trained in step 1.
5. `demo_run_adv_training.sh` - Train a new adversarial defended model on dataset created in step 4. Run on test data afterwards.

### Changelog
 - Updated `MLproject` user parameters to add in the respective patch attack job parameters.
     - In `MLproject`, the `fgm.py` script is replaced with the `patch.py` script.
 - `patch.py` script follows the original fgm script, with an additional section of code in the `patch_attack` function to save patch results in addition to adversarial images.
    - Additional job parameters for the patch script are also passed into the `attack.py` script for processing.
 - `attacks.py` has been updated to run the patch attack instead of the fgm attack.
    - Additional code has been added to save patches in addition to adversarial images.
 - Updated `docker-compose.yml`, following recommendations to use a custom network.
    - Users must also update container names so they are unique along with the demo scripts (network name must be set here too).
 - The `train.py` script has been updated to automatically store a registered model from training into the MLFlow interface.
 - Additional entry points are included to allow for greater control over patch deployment and model-dataset testing.

