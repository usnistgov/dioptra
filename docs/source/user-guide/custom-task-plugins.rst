.. _user-guide-custom-task-plugins:

Custom Task Plugins
===================

When designing a custom example, you may be required to create a new task plugin in order to effect specific behaviors not included in the core plugins.
For additional examples on how these plugins are constructed, you can refer to examples/tensorflow-mnist-classifier/src/tasks.py.

Creating a Basic Task
---------------------

The testbed utilizes Prefect library for task creation.
Tasks represent discreet actions in a workflow, and work like a function.
They take inputs, perform an action, and return an optional result.
Use the @task decorator before a function definition to create a new task:

.. code-block:: python

   from prefect import task

   @task
   def add_values(x,y):
       return x + y

It is generally best practice to create small tasks, atomizing your workflow down to discrete units of work.
Those tasks may then be chained together.
Tasks can be as complex as needed with no ill effect.
For a slightly more complex task, consider the sample below, which will generate random samples according to the parameters you set.

.. code-block:: python

   @task
   def draw_random_integers(
       rng: RNGenerator,
       low: int = 0,
       high: int = 2 ** 31 - 1,
       size: Optional[Union[int, Tuple[int, ...]]] = None,
   ) -> np.ndarray:
       size = size or 1
       result: np.ndarray = rng.integers(low=low, high=high, size=size)

       return result


Chaining Tasks with Flow
------------------------

Once your tasks have been created, your entrypoint must create a prefect Flow (workflow) that defines how the tasks are to be executed.
Note: Prefect Flows are not to be confused with MLflow.
Refer to the fgm.py entrypoint below for an example:

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

           # ...
           # Truncated
           # ...

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

In this sample, you can see that each invocation of :py:func:`.pyplugs.call_task` calls a unique task.
The arguments for each case are (directory, python_script, task, task_arguments).
This sample references plugins that are included in the core testbed plugins package, but you are not limited to those.
Imagine a custom plugin named ``squeeze_plugin.py`` written in the src directory of the feature_squeeze_mnist example:

.. code-block:: python

   feature_squeeze = pyplugs.call_task(
       "src",
       "squeeze_plugin",
       "feature_squeeze",
       # ... Additional arguments ...
   )
