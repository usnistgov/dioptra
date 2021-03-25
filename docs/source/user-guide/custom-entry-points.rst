.. _user-guide-custom-entry-points:

Creating a New Entry Point
==========================

When designing a custom example, it can be helpful to create or modify entry points, which are essentially parameterized execution flows that perform various functions and are accessible from the REST API.

MLProject File
--------------

In the `MLProject` file, there is a list of available entry points which are made available to the REST API.

.. code-block:: yaml

   entry_points:
     fgm:
      parameters:
        data_dir: { type: path, default: "/nfs/data" }
        image_size: { type: string, default: "28,28,1" }
        adv_tar_name: { type: string, default: "testing_adversarial_fgm.tar.gz" }
        adv_data_dir: { type: string, default: "adv_testing" }
        model_name: { type: string, default: "mnist_le_net" }
        model_version: { type: string, default: "1" }
        batch_size: { type: float, default: 32 }
        eps: { type: float, default: 0.3 }
        eps_step: { type: float, default: 0.1 }
        minimal: { type: float, default: 0 }
        norm: { type: string, default: "inf" }
        seed: { type: float, default: -1 }
      command: >
        python src/fgm.py
        --data-dir {data_dir}
        --image-size {image_size}
        --adv-tar-name {adv_tar_name}
        --adv-data-dir {adv_data_dir}
        --model-name {model_name}
        --model-version {model_version}
        --batch-size {batch_size}
        --eps {eps}
        --eps-step {eps_step}
        --minimal {minimal}
        --norm {norm}
        --seed {seed}

     infer:
      parameters:
        run_id: { type: string }
        image_size: { type: string, default: "28,28,1" }
        model_name: { type: string, default: "mnist_le_net" }
        model_version: { type: string, default: "1" }
        adv_tar_name: { type: string, default: "testing_adversarial_fgm.tar.gz" }
        adv_data_dir: { type: string, default: "adv_testing" }
        seed: { type: float, default: -1 }
      command: >
        python src/infer.py
        --run-id {run_id}
        --image-size {image_size}
        --model-name {model_name}
        --model-version {model_version}
        --adv-tar-name {adv_tar_name}
        --adv-data-dir {adv_data_dir}
        --seed {seed}

     train:
      parameters:
        data_dir: { type: path, default: "/nfs/data" }
        image_size: { type: string, default: "28,28,1" }
        model_architecture: { type: string, default: "le_net" }
        epochs: { type: float, default: 30 }
        batch_size: { type: float, default: 32 }
        register_model_name: { type: string, default: "" }
        learning_rate: { type: float, default: 0.001 }
        optimizer: { type: string, default: "Adam" }
        validation_split: { type: float, default: 0.2 }
        seed: { type: float, default: -1 }
      command: >
        python src/train.py
        --data-dir {data_dir}
        --image-size {image_size}
        --model-architecture {model_architecture}
        --epochs {epochs}
        --batch-size {batch_size}
        --register-model-name {register_model_name}
        --learning-rate {learning_rate}
        --optimizer {optimizer}
        --validation-split {validation_split}
        --seed {seed}

For example, in the `tensorflow-mnist-classifier` example, there are three entry points.
The `train` entry point can be used to train a new model on MNIST images.
The `fgm` entry point can be used to attack a model and generate adversarial examples based on the model, and the `infer` entry point can be used to test those adversarial examples against a model.

For each of these entry points, a number of parameters and defaults are specified, as well as the location of the python script that will process these parameters.

Parameters
~~~~~~~~~~

Using the `fgm` entry point as an example, it has a number of parameters which are used to configure the attack.

- data_dir: a directory containing clean images
- image_size: the shape (height, width, channels) of the images in the directory
- adv_tar_name: the name of the tarfile which will contain the adversarial images
- adv_data_dir: the directory to use when saving the adversarially generated images
- model_name: the name of the model artifact to attack in MLFlow
- model_version: the version of the model artifact to attack in MLFlow
- batch_size: the size of the batch on which adversarial samples are generated
- eps - FGM attack step size
- eps_step - The step size of the input variation for the minimal perturbation computation
- minimal - If True, compute the minimal perturbation, and use eps_step for the step size and eps for the maximum perturbation.
- norm - FGM attack norm of adversarial perturbation
- seed - Entry point RNG seed

Of these, many parameters are common among different attacks.
For example other evasion attacks may still need `data_dir`, `image_size`, `adv_data_dir`, `adv_tar_name`, `model_name`, `model_version`, `batch_size` and seed.
But the FGM attack has attack specific parameters `eps`, `eps_step`, `minimal` and `norm`, which may need to be removed, depending on the type of entry point being created.

Script
------

Click Options
~~~~~~~~~~~~~

The parameters specified in the MLProject file are passed via click to the function `fgm_attack()` in `fgm.py`.
`fgm_attack()` is defined as a click command, and a series of click options are defined noting the type of each parameter, the name, a description of the parameter, and a default value.

When creating a new entry point, one should develop a similar click command with the parameters specified as click options, and call that function from the python main thread, as is done in `fgm.py`.
This command is responsible for providing parameters to the various components of the custom entry points, and for chaining outputs between various plugins.

fgm.py - Using Plugins
----------------------

Below is `fgm.py`, without the imports. This section will include an in

.. code-block:: python

   _PLUGINS_IMPORT_PATH: str = "securingai_builtins"
   DISTANCE_METRICS: List[Dict[str, str]] = [
      {"name": "l_infinity_norm", "func": "l_inf_norm"},
      {"name": "l_1_norm", "func": "l_1_norm"},
      {"name": "l_2_norm", "func": "l_2_norm"},
      {"name": "cosine_similarity", "func": "paired_cosine_similarities"},
      {"name": "euclidean_distance", "func": "paired_euclidean_distances"},
      {"name": "manhattan_distance", "func": "paired_manhattan_distances"},
      {"name": "wasserstein_distance", "func": "paired_wasserstein_distances"},
   ]

The above is a list of distance metrics, which are primarily used in this example to measure how similar the adversarial images are to the original images.
This makes use of metrics defined in `/task-plugins/securingai_builtins/metrics.py`.
These may or may not be useful depending on the type of entry point being defined.

In the case of non-adversarial entry points, these will not be useful, as there would be nothing to compare.
Similarly, for attacks which do not produce adversarial images, such as model inversion, or membership inference attacks, these may be less useful as metrics.

.. code-block:: python

   LOGGER: BoundLogger = structlog.stdlib.get_logger()


   def _map_norm(ctx, param, value):
      norm_mapping: Dict[str, float] = {"inf": np.inf, "1": 1, "2": 2}
      processed_norm: float = norm_mapping[value]

      return processed_norm


   def _coerce_comma_separated_ints(ctx, param, value):
      return tuple(int(x.strip()) for x in value.split(","))


   def _coerce_int_to_bool(ctx, param, value):
      return bool(int(value))

.. code-block:: python

   @click.command()
   @click.option(
      "--data-dir",
      type=click.Path(
         exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
      ),
      help="Root directory for NFS mounted datasets (in container)",
   )

   @click.option(
      "--image-size",
      type=click.STRING,
      callback=_coerce_comma_separated_ints,
      help="Dimensions for the input images",
   )
   @click.option(
      "--adv-tar-name",
      type=click.STRING,
      default="testing_adversarial_fgm.tar.gz",
      help="Name to give to tarfile artifact containing fgm images",
   )
   @click.option(
      "--adv-data-dir",
      type=click.STRING,
      default="adv_testing",
      help="Directory for saving fgm images",
   )
   @click.option(
      "--model-name",
      type=click.STRING,
      help="Name of model to load from registry",
   )
   @click.option(
      "--model-version",
      type=click.STRING,
      help="Version of model to load from registry",
   )
   @click.option(
      "--batch-size",
      type=click.INT,
      help="Batch size to use when training a single epoch",
      default=32,
   )
   @click.option(
      "--eps",
      type=click.FLOAT,
      help="FGM attack step size (input variation)",
      default=0.3,
   )
   @click.option(
      "--eps-step",
      type=click.FLOAT,
      help="FGM attack step size of input variation for minimal perturbation computation",
      default=0.1,
   )
   @click.option(
      "--minimal",
      type=click.Choice(["0", "1"]),
      callback=_coerce_int_to_bool,
      help="If 1, compute the minimal perturbation using eps_step for the step size and "
      "eps for the maximum perturbation.",
      default="0",
   )
   @click.option(
      "--norm",
      type=click.Choice(["inf", "1", "2"]),
      default="inf",
      callback=_map_norm,
      help="FGM attack norm of adversarial perturbation",
   )
   @click.option(
      "--seed",
      type=click.INT,
      help="Set the entry point rng seed",
      default=-1,
   )

The above click options define parameters for the function below.
As mentioned earlier, some of these options will be common to other evasion attacks.
In particular, the `eps`, `eps_step`, `minimal` and `norm` parameters are somewhat specific to the FGM example.
While they may be present in some other attacks, attacks such as the pixel threshold attack would not need these parameters.

.. code-block:: python

   def fgm_attack(
      data_dir,
      image_size,
      adv_tar_name,
      adv_data_dir,
      model_name,
      model_version,
      batch_size,
      eps,
      eps_step,
      minimal,
      norm,
      seed,
   ):
      LOGGER.info(
         "Execute MLFlow entry point",
         entry_point="fgm",
         data_dir=data_dir,
         image_size=image_size,
         adv_tar_name=adv_tar_name,
         adv_data_dir=adv_data_dir,
         model_name=model_name,
         model_version=model_version,
         batch_size=batch_size,
         eps=eps,
         eps_step=eps_step,
         minimal=minimal,
         norm=norm,
         seed=seed,
      )

      with mlflow.start_run() as active_run:  # noqa: F841
         flow: Flow = init_fgm_flow()
         state = flow.run(
            parameters=dict(
               testing_dir=Path(data_dir) / "testing",
               image_size=image_size,
               adv_tar_name=adv_tar_name,
               adv_data_dir=(Path.cwd() / adv_data_dir).resolve(),
               distance_metrics_filename="distance_metrics.csv",
               model_name=model_name,
               model_version=model_version,
               batch_size=batch_size,
               eps=eps,
               eps_step=eps_step,
               minimal=minimal,
               norm=norm,
               seed=seed,
            )
         )

      return state

The above function initializes an MLFlow flow using the function below.
This essentially makes use of the pyplugs task system to chain outputs and inputs between existing plugins.

.. code-block:: python

   def init_fgm_flow() -> Flow:
      with Flow("Fast Gradient Method") as flow:
         (
            testing_dir,
            image_size,
            adv_tar_name,
            adv_data_dir,
            distance_metrics_filename,
            model_name,
            model_version,
            batch_size,
            eps,
            eps_step,
            minimal,
            norm,
            seed,
         ) = (
            Parameter("testing_dir"),
            Parameter("image_size"),
            Parameter("adv_tar_name"),
            Parameter("adv_data_dir"),
            Parameter("distance_metrics_filename"),
            Parameter("model_name"),
            Parameter("model_version"),
            Parameter("batch_size"),
            Parameter("eps"),
            Parameter("eps_step"),
            Parameter("minimal"),
            Parameter("norm"),
            Parameter("seed"),
         )
         seed, rng = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "rng", "init_rng", seed=seed
         )
         tensorflow_global_seed = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "sample", "draw_random_integer", rng=rng
         )
         dataset_seed = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "sample", "draw_random_integer", rng=rng
         )

The above plugin calls initialize the tensorflow random number generator.
The call_task function refers to a specific function declared as a plugin.
For example, the `draw_random_integer()` function is defined in `task-plugins/securingai_builtins/random/sample.py`.

.. code-block:: python

         init_tensorflow_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.backend_configs",
            "tensorflow",
            "init_tensorflow",
            seed=tensorflow_global_seed,
         )
         make_directories_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "make_directories",
            dirs=[adv_data_dir],
         )

The above plugin call initializes the directory being used to save adversarial images, if it doesn't already exist.

.. code-block:: python

         log_mlflow_params_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.tracking",
            "mlflow",
            "log_parameters",
            parameters=dict(
               entry_point_seed=seed,
               tensorflow_global_seed=tensorflow_global_seed,
               dataset_seed=dataset_seed,
            ),
         )
         keras_classifier = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.registry",
            "art",
            "load_wrapped_tensorflow_keras_classifier",
            name=model_name,
            version=model_version,
            upstream_tasks=[init_tensorflow_results],
         )

The above plugin call loads the model artifact from MLFlow.

.. code-block:: python

         distance_metrics_list = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.metrics",
            "distance",
            "get_distance_metric_list",
            request=DISTANCE_METRICS,
         )
         distance_metrics = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.attacks",
            "fgm",
            "create_adversarial_fgm_dataset",
            data_dir=testing_dir,
            keras_classifier=keras_classifier,
            distance_metrics_list=distance_metrics_list,
            adv_data_dir=adv_data_dir,
            batch_size=batch_size,
            image_size=image_size,
            eps=eps,
            eps_step=eps_step,
            minimal=minimal,
            norm=norm,
            upstream_tasks=[make_directories_results],
         )

The above plugin call makes use of the FGM attack plugin, located at `task-plugins/securingai_builtins/attacks/fgm.py`.
When creating a new attack entry point, it may be useful to create custom task plugins, particularly for adding a new attack.
This is described in the next section. Alternatively, this plugin reference can simply be replaced with a normal imported function.

.. code-block:: python

         log_evasion_dataset_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_directory_as_tarball_artifact",
            source_dir=adv_data_dir,
            tarball_filename=adv_tar_name,
            upstream_tasks=[distance_metrics],
         )

The above plugin call bundles the adversarial dataset as a tarball and makes it available as a downloadable artifact in MLFlow.

.. code-block:: python

         log_distance_metrics_result = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_data_frame_artifact",
            data_frame=distance_metrics,
            file_name=distance_metrics_filename,
            file_format="csv.gz",
            file_format_kwargs=dict(index=False),
         )

      return flow

The above plugin call logs the distance metrics results to MLFlow.
As mentioned earlier, while many evasion attacks can make use of these distance metrics, for other attacks such as model inference or model inversion these may not be as useful, and it may be helpful to add metrics as plugins or create custom metrics.

.. code-block:: python

   if __name__ == "__main__":
      log_level: str = os.getenv("AI_JOB_LOG_LEVEL", default="INFO")
      as_json: bool = True if os.getenv("AI_JOB_LOG_AS_JSON") else False

      clear_logger_handlers(get_prefect_logger())
      attach_stdout_stream_handler(as_json)
      set_logging_level(log_level)
      configure_structlog()

      with plugin_dirs(), StdoutLogStream(as_json), StderrLogStream(as_json):
         _ = fgm_attack()

This main section primarily serves to begin the fgm attack flow, and is directly executed when selecting the `fgm` entry point as a parameter to the REST API.
