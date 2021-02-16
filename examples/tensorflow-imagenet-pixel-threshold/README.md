# Tensorflow ImageNet Pixel Threshold Demo

>⚠️ **Warning:** This demo assumes that you have access to an on-prem deployment of the Securing AI Testbed that provides a copy of the ImageNet dataset and a CUDA-compatible GPU.
> This demo cannot be run on a typical personal computer.

The demo provided in the Jupyter notebook `demo.ipynb` uses the Securing AI Testbed to run experiments that investigate the effects of the pixel threshold attack when launched on a neural network model trained on the ImageNet dataset.

## Getting started

To run the demo on an on-prem deployment, all you need to do is download and start the **jupyter** service defined in this example's `docker-compose.yml` file.
Open a terminal and navigate to this example's directory and run the **jupyter** startup sequence,

```bash
make jupyter
```

Once the startup process completes, open up your web browser and enter http://localhost:38888 in the address bar to access the Jupyter Lab interface (if nothing shows up, wait 10-15 more seconds and try again).
Double click the `work` folder and open the `demo.ipynb` file.
From here, follow the provided instructions to run the demo provided in the Jupyter notebook.

When you are done running the demo, close the browser tab containing this Jupyter notebook and shut down the services by running `make teardown` on the command-line.
