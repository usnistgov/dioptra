# Tensorflow Road Signs YOLO Demo

>⚠️ **Warning:** This demo assumes that you have access to an on-prem deployment of Dioptra that provides a copy of the Road Signs dataset and a CUDA-compatible GPU.
> This demo cannot be run on a typical personal computer.

The demo provided in the Jupyter notebook `demo.ipynb` contains an example of how to set up and train a model based on the YOLO v1 architecture and use it to perform object detection on the Road Signs dataset.

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
