# Tensorflow MNIST Classifier demo

![Lab architecture diagram](securing_ai_lab_architecture.png)

This demo provides a practical example that shows how the Securing AI Lab Architecture can be used to run a simple experiment on the transferability of the fast gradient method (FGM) evasion attack between two neural network architectures.
It can be used as a basic template for crafting your own custom scripts to run within the architecture.

## Getting started

The step-by-step demo is provided in the Jupyter notebook format in the file `demo.ipynb`.
The easiest way to get up and running with the Jupyter notebook is to install a recent version of Anaconda on your host machine.
Links for installing version 2020.11 are provided below,

-   Anaconda for Windows: <https://repo.anaconda.com/archive/Anaconda3-2020.11-Windows-x86_64.exe>

-   Anaconda for Mac: <https://repo.anaconda.com/archive/Anaconda3-2020.11-MacOSX-x86_64.pkg>

-   Anaconda for Linux: <https://repo.anaconda.com/archive/Anaconda3-2020.11-Linux-x86_64.sh>

After installing Anaconda, use the `environment.yml` file distributed with this example to set up a virtual environment that can be used to run the notebook and also execute the code under the `src/` directory if you want to try it out locally.
To create the virtual environment and install the necessary dependencies, run

```bash
conda env create --file environment.yml
```

To activate the environment, run,

```bash
conda activate tensorflow-mnist-classifier
```

To start up Jupyter Lab, which you can use to view and execute the Jupyter notebook, run,

```bash
jupyter lab
```

Please note, if this is your first time using this demo, then you will need to initialize the database.
Initializing the database can be done using the `Makefile`,

```bash
make initdb
```

You should now be able to start running the demo provided in the Jupyter notebook.
