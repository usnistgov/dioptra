# Tensorflow Adversarial Patch Demo

> [!CAUTION]
> **DEPRECATED**
>
> This example is obsolete and will not work with the v1.0.0 release of Dioptra. It is
> retained for reference only. It may be ported to work with v1.0.0 in the future.

>⚠️ **Warning:** The attack used in this demo is computationally expensive and will take a very long to complete if run using the CPUs found in a typical personal computer.
> For this reason, it is necessary that you run these demos on a CUDA-compatible GPU.

This demo provides three different versions of the adversarial patch attack on separate image classification datasets and model architectures.
The three available Jupyter notebooks explore the following poisoning attacks:

-   `demo-mnist-patches.ipynb`: Applies adversarial patch attack on the MNIST dataset. Includes preprocessing and adversarial training defenses.
-   `demo-fruits360-patches.ipynb`: Applies adversarial patch attack on Fruits360 dataset. Includes adversarial training defenses.
-   `demo-imagenet-patches.ipynb`: Applies attack on the ImageNet dataset. Uses a pretrained model with the `init_model` entrypoint, rather than train a new model with the `train` entrypoint.

Users are welcome to run the demos in any order.
The MNIST demo takes the shortest time to complete and contains an additional set of defense examples.
For more information regarding attack and defense parameters, please see the attack and defense sections of the [MLflow Entrypoint Overview](#MLflow-Entrypoint-Overview) section.

Users can also explore the following preprocessing defenses from their associated defense entry points:

-   Spatial Smoothing: Smooths out an image by passing a median filter through neighboring pixel values in images.
-   Gaussian Augmentation: Adds gaussian noise to an image.
-   JPEG Compression: Applies an image compression algorithm over the image.

Please note that the patch attack generally bypasses most preprocessing defenses, see `demo-mnist-patches.ipynb` for details.


## Running the example

To prepare your environment for running this example, follow the linked instructions below:

1.  [Create and activate a Python virtual environment and install the necessary dependencies](../README.md#creating-a-virtual-environment)
2.  [Download the MNIST dataset using the download_data.py script.](../README.md#downloading-datasets)
3.  [Follow the links in these User Setup instructions](../../README.md#user-setup) to do the following:
    -   Build the containers
    -   Use the cookiecutter template to generate the scripts, configuration files, and Docker Compose files you will need to run Dioptra
4.  [Edit the docker-compose.yml file to mount the data folder in the worker containers](../README.md#mounting-the-data-folder-in-the-worker-containers)
5.  [Initialize and start Dioptra](https://pages.nist.gov/dioptra/getting-started/running-dioptra.html#initializing-the-deployment)
6.  [Register the custom task plugins for Dioptra's examples and demos](../README.md#registering-custom-task-plugins)
7.  [Register the queues for Dioptra's examples and demos](../README.md#registering-queues)
8.  [Start JupyterLab and open `demo.ipynb`](../README.md#starting-jupyter-lab)

Steps 1–4 and 6–7 only need to be run once.
**Returning users only need to repeat Steps 5 (if you stopped Dioptra using `docker compose down`) and 8 (if you stopped the `jupyter lab` process)**.


## MLflow Entrypoint Overview

Here are the available MLflow entry points used by the demos and their associated parameters.

### Common Training and Testing Entry Points

-   `init_model`: Loads a pretrained model available from the TensorFlow library into the MLflow model storage. Evaluates the model on an available test set
    -   Parameters:
        -   `data_dir` : The directory of the test set for evaluating pretrained model.
        -   `image_size`: A tuple specifying default image size.
        -   `register_model_name`: Specifies trained model name.
        -   `model_architecture`: Specifies model type (Current options: "resnet50", "vgg16").
        -   `batch_size`: Specifies a positive integer batch size for image testing.
        -   `seed`: Specifies an integer seed value for controlling randomized tensorflow behavior.
        -   `imagenet_preprocessing`: If set to true, apply keras ImageNet preprocessing settings for images.

-   `infer`:  Loads and evaluates an model from MLflow storage on a test set created from another MLflow run.
    -   Parameters:
        -   `run_id`: The string ID of the associated MLflow run.
        -   `image_size`: A tuple specifying default image size.
        -   `model_name`: The name of the associated model.
        -   `model_version`: The version of the associated model. Use `none` for latest version.
        -   `batch_size`: Specifies batch size of image testing.
        -   `seed`: Specifies an integer seed value for controlling randomized tensorflow behavior.
        -   `adv_tar_name`: Specifies the tarfile name for the dataset artifact.
        -   `adv_data_dir`: Specifies the folder name containing the dataset artifact.
        -   `imagenet_preprocessing`: If set to true, apply keras ImageNet preprocessing settings for images.
    -   Additional Notes:
        -   Most data preprocessing steps and attack deployment steps will generate a data artifact (ex. `adv_testing.tar`) which will contain the specified dataset of interest (ex `adversarial_patched_data`).
        -   Users must specify the artifact tarfile and dataset name in order to properly transfer the inputs between job runs.

-   `train`: Trains a model architecture over a given dataset.
    -   Parameters:
        -   `register_model_name`: Specifies trained model name.
        -   `data_dir_training`: Training data directory.
        -   `data_dir_testing`: Testing data directory.
        -   `model_architecture`: Specifies model type (Current options: "le_net","shallow_net", "alex_net", "resnet50", "vgg16")
        -   `epochs`: Specifies a positive floating point number of iterations through the given dataset.
        -   `batch_size`: Positive integer batch size for training and testing.
        -   `learning_rate`: Initial learning rate for the training step. Positive floating point values only.
        -   `optimizer`: Model optimization algorithm (Current options:"rmsprop", "adam", "adagrad", "sgd")
        -   `validation_split`: Amount of training data to split off as the validation set. Range is 0 to 1.0.
        -   `load_dataset_from_mlruns`: If set to true, loads the dataset from the MLflow experiment artifacts repo instead.
        -   `dataset_run_id_testing`: The string ID of the associated MLflow run for testing. Can be left blank to use `data_dir_testing` instead.
        -   `dataset_run_id_training`: The string ID of the associated MLflow run for training. Must be instantiated if user sets `load_dataset_from_mlruns` to true.
        -   `adv_tar_name`: Specifies the tarfile name for the dataset artifact.
        -   `adv_data_dir`: Specifies the folder name containing the dataset artifact.
        -   `seed`: Specifies an integer seed value for controlling randomized tensorflow behavior.
        -   `imagenet_preprocessing`: If set to true, apply keras ImageNet preprocessing settings for images.
    -   Additional Notes:
        -   When `load_dataset_from_mlruns` is set to true, the provided data artifact is used over the default dataset location.
        -   As a result the `dataset_run_id_training`, `adv_tar_name`, and `adv_data_dir` parameters must be provided when `load_dataset_from_mlruns` is true. If false, they are not used in the job.

### Patch Attack Entry Points

-   `gen_patch`: Generates adversarial patches from a trained model and dataset.
    -   Parameters:
        -   `data_dir`: Sample data directory for generating adversarial patches.
        -   `image_size`: A tuple specifying default image size.
        -   `model_name`: The name of the associated model.
        -   `model_version`: The version of the associated model. Use `none` for latest version.
        -   `adv_tar_name`: Specifies the output tarfile name for the patch artifact.
        -   `adv_data_dir`: Specifies the output folder name containing the patch artifact.
        -   `learning_rate`: Positive floating point value for patch optimization.
        -   `max_iter`: Maximum number of patch optimization steps. Positive integer values only.
        -   `patch_target`: Target integer class index for patch attack.
        -   `num_patch`: Number of patches to generate.
        -   `num_patch_gen_samples`: Number of images to use for optimizing each patch.
        -   `imagenet_preprocessing`: If set to true, apply keras ImageNet preprocessing settings for images.
        -   `seed`: Specifies an integer seed value for controlling randomized tensorflow behavior.

-   `deploy_patch`: Deploys adversarial patches to a given dataset.
    -   Parameters:
        -   `run_id`: The string ID of the associated MLflow run.
        -   `data_dir`:  Sample data directory for applying adversarial patches.
        -   `model`: The name of the associated trained model.
        -   `model_architecture`: Specifies model type (Current options: "le_net","shallow_net", "alex_net", "resnet50", "vgg16").
        -   `patch_deployment_method`: If set to "corrupt", patched-images replace their original versions. If set to "augment", patched-images are stored alongside their original counterparts.
        -   `patch_application_rate`: Specifies fraction from \[0, 1.0\] of dataset to apply patches over. A value of 1.0 results in the patch applied over the entire dataset.
        -   `patch_scale`: Floating point value from \[0, 1.0\] specifying patch size relative to image. Setting this value to 1.0 effectively replaces the entire image with a patch.
        -   `batch_size`: Integer batch size of patch deployment over images.
        -   `rotation_max`: Floating point value from \[0, 180\] degrees specifying maximum, randomized patch rotation.
        -   `scale_min`: Floating point value from \[0, 1.0) degrees specifying minimum random scaling. Must be smaller than `scale_max`.
        -   `scale_max`: Floating point value from (0, 1.0\] degrees specifying maximum random scaling. Must be larger than `scale_min`.
        -   `seed`: Specifies an integer seed value for controlling randomized tensorflow behavior.
    -   Additional Notes:
        -   Patches are effectively rotated a randomized amount within `rotation_max` degrees and will be scaled by a value between \[`scale_min`, `scale_max`\].

### Image Preprocessing Defense Entry Points

-   `spatial_smoothing`: Applies localized median filtering across an image for the given dataset.
    -   Parameters:
        -   `data_dir`: Directory of target dataset.
        -   `model`: Name of trained model stored in MLflow repo.
        -   `model_architecture`: Specifies model type (Current options: "le_net","shallow_net", "alex_net", "resnet50", "vgg16")
        -   `batch_size`: Batch size for input images. Positive integer values only.
        -   `spatial_smoothing_window_size`: Size of median filtering window. Positive integer values only.
        -   `spatial_smoothing_apply_fit`: If true, set to training data filtering.
        -   `spatial_smoothing_apply_predict`: If true, set to testing data filtering.
        -   `load_dataset_from_mlruns`: If true, load dataset from an MLflow run instead.
        -   `dataset_run_id`: The string ID of the associated MLflow run.
        -   `dataset_tar_name`: Name of tarfile for stored dataset.
        -   `dataset_name`: Folder name of stored dataset.
        -   `seed`: Specifies an integer seed value for controlling randomized tensorflow behavior.

-   `jpeg_compression`: Applies image compression onto the given dataset.
    -   Parameters:
        -   `data_dir`: Directory of target dataset.
        -   `model`: Name of trained model stored in MLflow repo.
        -   `model_architecture`: Specifies model type (Current options: "le_net","shallow_net", "alex_net", "resnet50", "vgg16")
        -   `batch_size`: Batch size for input images. Positive integer values only.
        -   `jpeg_compression_channels_first`: Specifies whether to apply channels first (true) or last (false).
        -   `jpeg_compression_quality`: Controls quality of image compression from 1 (worst) to 100 (best) in integer values. Recommend values of 95 or lower.
        -   `jpeg_compression_apply_fit`: If true, set to training data compression.
        -   `jpeg_compression_apply_predict`: If true, set to testing data compression.
        -   `load_dataset_from_mlruns`: If true, load dataset from an MLflow run instead.
        -   `dataset_run_id`: The string ID of the associated MLflow run.
        -   `dataset_tar_name`: Name of tarfile for stored dataset.
        -   `dataset_name`: Folder name of stored dataset.
        -   `seed`: Specifies an integer seed value for controlling randomized tensorflow behavior.

-   `gaussian_augmentation`: Applies gaussian noise over a given dataset.
    -   Parameters:
        -   `data_dir`: Directory of target dataset.
        -   `model`: Name of trained model stored in MLflow repo.
        -   `model_architecture`: Specifies model type (Current options: "le_net","shallow_net", "alex_net", "resnet50", "vgg16")
        -   `batch_size`: Batch size for input images. Positive integer values only.
        -   `gaussian_augmentation_perform_data_augmentation`: If set to true, include original test data as well.
        -   `gaussian_augmentation_ratio`: With data augmentation on, specifies ratio from \[0.0, 1.0\] of poisoning examples to add. A value of 1.0 results in the defense applied over the entire dataset.
        -   `gaussian_augmentation_sigma`: Controls the standard deviation of the noise. Higher floating-point values result in greater noise added.
        -   `gaussian_augmentation_apply_fit`: Apply noise to training set.
        -   `gaussian_augmentation_apply_predict`: Apply noise to testing set.
        -   `load_dataset_from_mlruns`: If true, load dataset from an MLflow run instead.
        -   `dataset_run_id`: The string ID of the associated MLflow run.
        -   `dataset_tar_name`: Name of tarfile for stored dataset.
        -   `dataset_name`: Folder name of stored dataset.
        -   `seed`: Specifies an integer seed value for controlling randomized tensorflow behavior.
