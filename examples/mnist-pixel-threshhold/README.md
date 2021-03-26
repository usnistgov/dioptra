# Tensorflow MNIST Pixel Threshold demo

This demo adapts the [Tensorflow MNIST Classifier](../tensorflow-mnist-classifier) example to use the [Pixel Threshold](https://adversarial-robustness-toolbox.readthedocs.io/en/latest/modules/attacks/evasion.html#pixelattack) attack to generate adversarial examples.

## Quickstart

> :information_source: More detailed setup instructions are available in the [Tensorflow MNIST Classifier README](../tensorflow-mnist-classifier/README.md).

The step-by-step demo is provided in the Jupyter notebook format in the file `demo.ipynb`.
Before starting up the notebook for the first time, users need to first initialize the Testbed API's database,

```bash
make initdb
```

and also select the docker-compose file they wish to use for deploying the microservices,

```bash
# This assumes you have a Windows computer
cp docker-compose.win.yml docker-compose.yml
```

The demo notebook contains the rest of the instructions necessary to complete the demo.
To start up Jupyter Lab, which you can use to view and execute the Jupyter notebook, run,

```bash
jupyter lab
```
