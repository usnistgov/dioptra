# Dioptra Tutorials

The examples directory contains Dioptra tutorials in the form of Jupyter Notebooks. Complete the following steps to run Jupyter Notebook:

<!-- markdownlint-disable MD007 MD030 -->
- [Creating a virtual environment](#creating-a-virtual-environment)
- [Downloading Datasets](#downloading-datasets)
- [Starting Jupyter Notebook](#starting-jupyter-notebook)
<!-- markdownlint-enable MD007 MD030 -->

## Creating a virtual environment

It is recommended that you create a virtual environment to use to manage the dependencies needed to run the setup scripts and use the Jupyter notebooks provided with the examples.
Run the following after you have cloned this repository:

```sh
# Move into the examples folder of cloned repo
cd /path/to/dioptra/examples

# Create a new virtual environment at /path/to/dioptra/examples/.venv
uv venv

# Activate the virtual environment
source .venv/bin/activate

# Install the dependencies
uv pip install -r examples-setup-requirements.txt
```

## Downloading Datasets

Some tutorials may use external datasets that need to be downloaded and configured before running the tutorial. Datasets should be stored in the dataset directory mounted in your worker containers.

Dioptra provides the [examples/scripts/download_data.py](https://github.com/usnistgov/dioptra/blob/main/examples/scripts/download_data.py) script to simplify the download and organization of datasets. This script uses [tensorflow_datasets (tfds)](https://www.tensorflow.org/datasets/api_docs/python/tfds) as source of publicly-available datasets and to download and prepare the data for use.

To list the available datasets, run:

```
uv run ./examples/scripts/download_data.py list
```

Then, to download and add a dataset directly to the `/dioptra/data` directory, run:

```
uv run ./examples/scripts/download_data.py download --data-dir /dioptra/data DATASET_NAME
```

For the full list of options, run `uv run ./examples/scripts/download_data.py -h` to display the script's help message.

## Starting Jupyter Notebook

Each example is contained in a Jupyter notebook that interacts with your Dioptra instance.
To use the notebooks, [activate your virtual environment](#creating-a-virtual-environment) and start Jupyter Lab from the command line.

```bash
# Run this in the examples/ folder
jupyter notebook
```

Once Jupyter starts up and is visible in your web browser, use the file explorer to navigate to open the tutorial you want to try.
