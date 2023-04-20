# Dioptra Examples and Demos

<!-- markdownlint-disable MD007 MD030 -->
- [Creating a virtual environment](#creating-a-virtual-environment)
- [Downloading Datasets](#downloading-datasets)
  - [Prerequisites](#prerequisites)
  - [Usage](#usage)
  - [Examples](#examples)
- [Registering Custom Task Plugins](#registering-custom-task-plugins)
  - [Prerequisites](#prerequisites-1)
  - [Usage](#usage-1)
  - [Examples](#examples-1)
- [Registering Queues](#registering-queues)
  - [Prerequisites](#prerequisites-2)
  - [Usage](#usage-2)
  - [Examples](#examples-2)
- [Mounting the data folder in the worker containers](#mounting-the-data-folder-in-the-worker-containers)
- [Starting Jupyter Lab](#starting-jupyter-lab)
<!-- markdownlint-enable MD007 MD030 -->

## Creating a virtual environment

It is recommended that you create a virtual environment to use to manage the dependencies needed to run the setup scripts and use the Jupyter notebooks provided with the examples.
Run the following after you have cloned this repository:

```sh
# Move into the examples folder of cloned repo
cd /path/to/dioptra/examples

# Create a new virtual environment at /path/to/dioptra/examples/.venv
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install the dependencies
python -m pip install -r ./scripts/venvs/examples-setup-requirements.txt
```

## Downloading Datasets

The download script [examples/scripts/download_data.py](./scripts/download_data.py) should be used to fetch the datasets used in Dioptra's examples and demos.
In addition to fetching the datasets, this script automatically organizes the files and directories so that each dataset follows a consistent and predictable structure.
The script can be used to download the following datasets:

-   [MNIST](http://yann.lecun.com/exdb/mnist/)
-   [Road Signs Detection (Kaggle)](https://www.kaggle.com/datasets/andrewmvd/road-sign-detection)
-   [Fruits 360 (Kaggle)](https://www.kaggle.com/datasets/moltean/fruits)
-   \[🚧 Under construction\] [ImageNet Object Localization Challenge (Kaggle)](https://www.kaggle.com/c/imagenet-object-localization-challenge)

### Prerequisites

[Create and activate the examples/.venv virtual environment](#creating-a-virtual-environment) if you have not already done so.
You will also need to register for a [Kaggle](https://kaggle.com) account and obtain an API token in order to fetch certain datasets.
For instructions on how to obtain and use a Kaggle API token, see <https://github.com/Kaggle/kaggle-api#api-credentials>.

### Usage

To run this script and download a dataset directly to a specific directory on your host machine, simply use the following:

```bash
python ./scripts/download_data.py --output /path/to/data/directory DATASET_NAME
```

For the full list of options and available datasets, run `python ./scripts/download_data.py -h` to display the script's help message:

    Usage: download_data.py [OPTIONS] COMMAND [ARGS]...

      Fetch a dataset used in Dioptra's examples and demos.

    Options:
      --output DIRECTORY            The path to the folder where the example
                                    datasets are stored. Defaults to the current
                                    working directory.
      --overwrite / --no-overwrite  Fetch the data even if the target folder
                                    already exists and overwrite any existing data
                                    files. By default the program will exit early
                                    if the target folder already exists.
      -h, --help                    Show this message and exit.

    Commands:
      fruits360  Fetch the Fruits 360 dataset hosted on Kaggle.
      imagenet   Fetch the ImageNet Object Localization Challenge dataset...
      mnist      Fetch the MNIST dataset.
      roadsigns  Fetch the Road Signs Detection dataset hosted on Kaggle.

Please note that some of the datasets have additional options that can be viewed by running `python ./scripts/download_data.py DATASET -h`.
For example, running `python ./scripts/download_data.py fruits360 -h` displays the help message for the Fruits 360 dataset shown below:

    Usage: download_data.py fruits360 [OPTIONS]

      Fetch the Fruits 360 dataset hosted on Kaggle.

      This downloader uses the Kaggle API and requires the use of an API token.
      For instructions on how to obtain and use a Kaggle API token, see
      https://github.com/Kaggle/kaggle-api#api-credentials.

    Options:
      --remove-zip / --no-remove-zip  Remove/keep the dataset zip file after
                                      extracting it. By default it will be
                                      removed.
      -h, --help                      Show this message and exit.

### Examples

```sh
# Downloads the MNIST dataset to /dioptra/data/Mnist, overwriting any existing files.
python ./scripts/download_data.py --output /dioptra/data --overwrite mnist

# Downloads the Road Signs Detection dataset to ./Road-Signs-Detection-v2. The
# script will stop early if the folder ./Road-Signs-Detection-v2 exists.
python ./scripts/download_data.py roadsigns

# Downloads the Fruits 360 dataset to /dioptra/data/Fruits360. The script will
# stop early and if the folder /dioptra/data/Fruits360 exists and the dataset
# zip file downloaded from Kaggle will not be removed.
python ./scripts/download_data.py --output /dioptra/data fruits360 --no-remove-zip
```

## Registering Custom Task Plugins

The script [examples/scripts/register_task_plugins.py](./scripts/register_task_plugins.py) should be used to register the custom task plugins used in Dioptra's examples and demos.

### Prerequisites

[Create and activate the examples/.venv virtual environment](#creating-a-virtual-environment) if you have not already done so.
You will also need to have an instance of Dioptra running, see [../cookiecutter-templates/cookiecutter-dioptra-deployment/README.md](../cookiecutter-templates/cookiecutter-dioptra-deployment/README.md) and the [Building the containers](https://pages.nist.gov/dioptra/getting-started/building-the-containers.html) and [Running Dioptra](https://pages.nist.gov/dioptra/getting-started/running-dioptra.html) sections of the published documentation for instructions.

### Usage

Run the following to register the custom task plugins used in Dioptra's examples and demos:

```bash
python ./scripts/register_task_plugins.py
```

For the full list of options, run `python ./scripts/register_task_plugins.py -h` to display the script's help message:

    Usage: register_task_plugins.py [OPTIONS]

      Register the custom task plugins used in Dioptra's examples and demos.

    Options:
      --plugins-dir DIRECTORY  The path to the directory containing the custom
                               task plugin subdirectories.  [default: ./task-
                               plugins]
      --api-url TEXT           The url to the Dioptra REST API.  [default:
                               http://localhost]
      -h, --help               Show this message and exit.

### Examples

```sh
# Registers the plugins to the REST API url https://dioptra.example.org
python ./scripts/register_task_plugins.py --api-url https://dioptra.example.org
```

## Registering Queues

The script [examples/scripts/register_queues.py](./scripts/register_queues.py) should be used to register the queues used in Dioptra's examples and demos.

### Prerequisites

[Create and activate the examples/.venv virtual environment](#creating-a-virtual-environment) if you have not already done so.
You will also need to have an instance of Dioptra running, see [../cookiecutter-templates/cookiecutter-dioptra-deployment/README.md](../cookiecutter-templates/cookiecutter-dioptra-deployment/README.md) and the [Building the containers](https://pages.nist.gov/dioptra/getting-started/building-the-containers.html) and [Running Dioptra](https://pages.nist.gov/dioptra/getting-started/running-dioptra.html) sections of the published documentation for instructions.

### Usage

Run the following to register the queues used in Dioptra's examples and demos:

```bash
python ./scripts/register_queues.py
```

For the full list of options, run `python ./scripts/register_queues.py -h` to display the script's help message:

    Usage: register_queues.py [OPTIONS]

      Register the queues used in Dioptra's examples and demos.

    Options:
      --queue TEXT    The queue name to register.  [default: tensorflow_cpu,
                      tensorflow_gpu, pytorch_cpu, pytorch_gpu]
      --api-url TEXT  The url to the Dioptra REST API.  [default:
                      http://localhost]
      -h, --help      Show this message and exit.

### Examples

```sh
# Registers the default queues to the REST API url https://dioptra.example.org
python ./scripts/register_queues.py --api-url https://dioptra.example.org

# Registers the queues tensorflow_cpu_highmem and tensorflow_gpu_highmem to the
# REST API at the default url http://localhost
python ./scripts/register_queues.py \
  --queue tensorflow_cpu_highmem --queue tensorflow_gpu_highmem
```

## Mounting the data folder in the worker containers

[In order to use the datasets you downloaded using the `download_data.py` script](#downloading-datasets), you will need to mount them into the worker containers.
However, [the `docker-compose.yml` file generated by the cookiecutter template](https://pages.nist.gov/dioptra/getting-started/running-dioptra.html#applying-the-template) does not mount any folders from your host machine into the worker containers.
To address this, open the `docker-compose.yml` file generated by the cookiecutter template in a text editor and find the blocks for the worker containers.
The worker container blocks will have **tfcpu**, **tfgpu**, **pytorch-cpu**, or **pytorch-gpu** in their names.
Append the line `- /path/to/data:/dioptra/data:ro` to the `volumes:` subsection.
An example is shown below.

> ⚠️ **Important!** Do not use `/path/to/data` verbatim, change it to the absolute path to data folder you created on your computer!

```yaml
dioptra-deployment-tfcpu-01:
  # Skipping unaffected lines in block
  volumes:
    - worker-ca-certificates:/usr/local/share/ca-certificates:rw
    - worker-etc-ssl:/etc/ssl:rw
    - /path/to/data:/dioptra/data:ro

dioptra-deployment-pytorchcpu-01:
  # Skipping unaffected lines in block
  volumes:
    - worker-ca-certificates:/usr/local/share/ca-certificates:rw
    - worker-etc-ssl:/etc/ssl:rw
    - /path/to/data:/dioptra/data:ro
```

If your data is stored in an NFS share and not on your local computer, please see [Mounting a folder on a NFS share](https://pages.nist.gov/dioptra/getting-started/running-dioptra.html#mounting-a-folder-on-an-nfs-share) in the Dioptra documentation.

## Starting Jupyter Lab

Each example is contained in a Jupyter notebook that interacts with your Dioptra instance.
To use the notebooks, [activate your virtual environment](#creating-a-virtual-environment) and start Jupyter Lab from the command line.

```bash
# Run this in the examples/ folder
jupyter lab
```

Once Jupyter Lab starts up and is visible in your web browser, use the file explorer to navigate to the example folder that you want to try and open the Jupyter notebook (it will usually be named `demo.ipynb`).
