# Tensorflow MNIST Pixel Threshold Demo

> ⚠️ **IMPORTANT!**
>
> This README is out of date and will be updated in the near future.
>
> There is a new setup tool that all users should use to configure and run Dioptra, please see the new sections [Building the containers](https://pages.nist.gov/dioptra/getting-started/building-the-containers.html) and [Running Dioptra](https://pages.nist.gov/dioptra/getting-started/running-dioptra.html) that have been added to the documentation.

The demo provided in the Jupyter notebook `demo.ipynb` uses Dioptra to run experiments that investigate the effects of the pixel threshold attack when launched on a neural network model trained on the MNIST dataset.

## Getting started

Everything you need to run this demo is packaged into a set of Docker images that you can obtain by opening a terminal, navigating to the root directory of the repository, and running `make pull-latest`.
Once you have downloaded the images, navigate to this directory using the terminal and run the demo startup sequence:

```bash
make demo
```

The startup sequence will take more time to finish the first time you use this demo, as you will need to download the MNIST dataset, initialize the Testbed API database, and synchronize the task plugins to the S3 storage.
Once the startup process completes, open up your web browser and enter `http://localhost:38888` in the address bar to access the Jupyter Lab interface (if nothing shows up, wait 10-15 more seconds and try again).
Double click the `work` folder and open the `demo.ipynb` file.
From here, follow the provided instructions to run the demo provided in the Jupyter notebook.

To watch the output logs for the Tensorflow worker containers as you step through the demo, run `docker-compose logs -f tfcpu-01 tfcpu-02` in your terminal.

When you are done running the demo, close the browser tab containing this Jupyter notebook and shut down the services by running `make teardown` on the command-line.
If you were watching the output logs, you will need to press <kbd>Ctrl</kbd>+<kbd>C</kbd> to stop following the logs before you can run `make teardown`.
