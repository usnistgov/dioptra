# Securing AI Lab Components
## ImageNet-ResetNet50 FGM and Spatial Smoothing Demo.

## Summary:

This demo is a variation of the original tensorflow-mnist demo, configured to run the FGM attack and spatial smoothing defense within the DGX workstation.
The steps follow the original guide with a few additional steps for launching the new attack and defense on ImageNet model and datasets.

Please see the [changelog](#changelog) section for a summary of general code changes made to this demo from the original tensorflow mnist demo.


### Mandatory: Setting container and network names for the demo.

Please replace `<username>` entry in the following files with your own personal user name:

```
demo_*.sh
docker-compose.yml
```

Alternatively: Run `find . \( ! -regex '.*/\..*' \) -type f | xargs sed -i 's/<username>/<YOUR_USER_NAME_HERE>/g'` to
automatically set the configured files with your username. Or use an IDE to update the scripts automatically.

## Some steps have been changed from the original mnist demo, as data download is replaced with NFS mount access.

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

* `make data` has been removed as we are now accessing the NFS mounted Fruits360 dataset.

NOTE: If the tarball upload triggers another permissions issue (i.e. "/work/*.tar.gz is not readable")

Run: `chmod 644 workflows.tar.gz`

To set the code tarball file to 'readable' for the S3 upload.

Then re-run: `make upload-job`

### Next: Launching GPU-configured docker jobs.

Right now, due to differences in docker vs docker-compose, GPU containers have to be manually executed via `docker run`
command. To simplify this, the following bash scripts have been provided:

1. `demo_train.sh`   - Loads, trains, and tests a lightweight model on a subset of the ImageNet dataset.
2. `demo_attack.sh`  - Launch an FGM attack on the model from step 1.
3. `demo_defense.sh` - Repeat step 2, but also launch a preprocessing defense to reduce model accuracy loss.


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





