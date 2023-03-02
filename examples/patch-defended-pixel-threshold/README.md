# Dioptra

> ⚠️ **IMPORTANT!**
>
> This README is out of date and will be updated in the near future.
>
> There is a new setup tool that all users should use to configure and run Dioptra, please see the new sections [Building the containers](https://pages.nist.gov/dioptra/getting-started/building-the-containers.html) and [Running Dioptra](https://pages.nist.gov/dioptra/getting-started/running-dioptra.html) that have been added to the documentation.

## ImageNet-Patch Demo.

## Summary:

This demo is a variation of the original tensorflow-mnist demo, configured to run the patch attack within the DGX workstation.
The steps follow the original guide with a few additional steps for launching patch attacks.

Please see the [changelog](#changelog) section for a summary of general code changes made to this demo from the original tensorflow mnist demo.


### Mandatory: Setting container and network names for the demo.

Please replace `<username>` entry in the following files with your own personal user name:

```
load_imagenet_model.sh
demo_run_attack.sh
docker-compose.yml
```

Alternatively: Run `find . \( ! -regex '.*/\..*' \) -type f | xargs sed -i 's/<username>/<YOUR_USER_NAME_HERE>/g'` to
automatically set the configured files with your username. Or use an IDE to update the scripts automatically.

## Some steps have been simplified from the original mnist demo, as data download is replaced with NFS mount access.

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

### Next: Setting up pretrained model and containers.

Run the following commands, from the tutorial session:


```
make services
make upload-job

```

* `make data` has been removed as we are now accessing the NFS mounted ImageNet dataset.

NOTE: If the tarball upload triggers another permissions issue (i.e. "/work/*.tar.gz is not readable")

Run: `chmod 644 workflows.tar.gz`

To set the code tarball file to 'readable' for the S3 upload.

Then re-run: `make upload-job`

### Next: Launching GPU-configured docker jobs.

Right now, due to differences in docker vs docker-compose, GPU containers have to be manually executed via `docker run`
command. To simplify this, the following bash scripts have been provided:

`load_imagenet_model.sh`
`demo_run_attack.sh`

Which will run the model setup and patch attacks respectively. The model
generated from the training script `load_imagenet_model.sh` is automatically stored in MLflow and used 

To run the patch attack script.
1. First run `load_imagenet_model.sh` to load a pretrained model.
5. Next run `demo_run_attack.sh`.


Please post in Slack if any issues were encountered, thanks!

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

The following changes are specific to ImageNet model and NFS dataset access.
 - Makefile has been updated so that `make data` is no longer called since is it not needed here.

 - In both `attacks.py`, `data.py` and `patch.py`:
    - Please note that the job parameters for the image size, color mode, rescale, and batch size are all updated for the ImageNet dataset.

  - `attacks.py` has been updated to use ImageNet settings for loading and configuring models.
    - The load keras model function has been updated to match the ART attack demo preprocessing settings for loading ImageNet images.
    - In line 137 of `attacks.py`, the random index generator is updated from 9 to 999 to account for the change in class size (10 to 1000).

 - `patch.py` has been updated to use the ImageNet nfs mount directory.
    - The job settings there contain updated documentation reflecting the new nfs filepath and ImageNet dataset options.
 - The attack and model setup .sh scripts also contain updated docker volume settings needed to mount the ImageNet dataset.
