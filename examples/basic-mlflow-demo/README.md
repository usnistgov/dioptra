# Securing AI Lab Components
## Basie MLFlow Demo.

## Summary:

This demo provides a basic example of example setup using MLflow entry points.
The follow steps will build and launch two customizable entrypoints, one demonstrating user parameter controls
and the second demonstrating basic model initialization and dataset access.


### Mandatory: Setting container and network names for the demo.

Please replace `<username>` entry in the following files with your own personal user name:

```
demo_*.sh
docker-compose.yml
```

Alternatively: Run `find . \( ! -regex '.*/\..*' \) -type f | xargs sed -i 's/<username>/<YOUR_USER_NAME_HERE>/g'` to
automatically set the configured files with your username. Or use an IDE to update the scripts automatically.


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

NOTE: If the tarball upload triggers another permissions issue (i.e. "/work/*.tar.gz is not readable")

Run: `chmod 644 workflows.tar.gz`

To set the code tarball file to 'readable' for the S3 upload.

Then re-run: `make upload-job`

### Next: Launching GPU-configured docker jobs.
The following scripts for manually launching jobs have been provided.

`first_demo.sh`
`second_demo.sh`

 In the first demo, the entrypoint for hello_world is linked to the hello_world.py script.
 Running this script will produce an MLflow log entry with a customizable log output string.
 Users can modify the hello-world entrypoint by adding/uncommenting `-P output_log_string=<CUSTOM TEXT>` onto the end of
 the job submission script. This alters the job property for `output_log_string` which is then passed from the entrypoint into the hello_world.py script as a command line argument.
 Additional fields can be created in MLflow and then passed into hello_world.py, by modifying the MLproject file,
 followed by the python Click input parameters in the hello_world.py script.

 In the second demo, a second python script `load_model_dataset.py` is linked to the load_model_dataset entrypoint.
 Running this demo will startup a basic pretrained ImageNet model, followed by an evaluation on the ImageNet dataset from
 our current server.







