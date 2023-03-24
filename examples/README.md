# Dioptra Examples and Demos

## Downloading Datasets

The download script [examples/scripts/download_data.py](./scripts/download_data.py) should be used to fetch the datasets used in Dioptra's examples and demos.
In addition to fetching the datasets, this script automatically organizes the files and directories so that each dataset follows a consistent and predictable structure.
The script can be used to download the following datasets:

-   [MNIST](http://yann.lecun.com/exdb/mnist/)
-   [Road Signs Detection (Kaggle)](https://www.kaggle.com/datasets/andrewmvd/road-sign-detection)
-   [Fruits 360 (Kaggle)](https://www.kaggle.com/datasets/moltean/fruits)
-   \[🚧 Under construction\] [ImageNet Object Localization Challenge (Kaggle)](https://www.kaggle.com/c/imagenet-object-localization-challenge)

### Prerequisites

See [examples/scripts/venvs/examples-setup-requirements.txt](./scripts/venvs/examples-setup-requirements.txt) for the list of packages that you need to have installed in order to use the download script.

You will also need to register for a [Kaggle](https://kaggle.com) account and obtain an API token in order to fetch certain datasets.
For instructions on how to obtain and use a Kaggle API token, see <https://github.com/Kaggle/kaggle-api#api-credentials>.

### Usage

It is recommended that you create a virtual environment to manage the script's dependencies.
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
