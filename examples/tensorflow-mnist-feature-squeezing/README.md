# Tensorflow MNIST Feature Squeezing Demo

>⚠️ **Warning:** Some of the attacks in this demo, _deepfool_ and _CW_ in particular, are computationally expensive and will take a very long to complete if run using the CPUs found in a typical personal computer.
> For this reason, it is highly recommended that you run these demos on a CUDA-compatible GPU.

The demo provided in the Jupyter notebook `demo.ipynb` uses Dioptra to run experiments that investigate the effectiveness of the feature-squeezing defense against a series of evasion attacks against a neural network model.

## Getting started

Everything you need to run this demo is packaged into a set of Docker images that you can obtain by opening a terminal, navigating to the root directory of the repository, and running `make pull-latest`.
Once you have downloaded the images, navigate to this example's directory using the terminal and run the demo startup sequence:

```bash
make demo
```

The startup sequence will take more time to finish the first time you use this demo, as you will need to download the MNIST dataset, initialize the Testbed API database, and synchronize the task plugins to the S3 storage.
Once the startup process completes, open up your web browser and enter `http://localhost:38888` in the address bar to access the Jupyter Lab interface (if nothing shows up, wait 10-15 more seconds and try again).
Double click the `work` folder and open the `demo.ipynb` file.
From here, follow the provided instructions to run the demo provided in the Jupyter notebook.

If you are running the demos locally and want to watch the output logs for the Tensorflow worker containers as you step through the demo, run `docker-compose logs -f tfcpu-01 tfcpu-02` in your terminal.

When you are done running the demo, close the browser tab containing this Jupyter notebook and shut down the services by running `make teardown` on the command-line.
If you were watching the output logs, you will need to press <kbd>Ctrl</kbd>-<kbd>C</kbd> to stop following the logs before you can run `make teardown`.
