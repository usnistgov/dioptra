import numpy as np
import structlog

from dioptra import pyplugs

LOGGER = structlog.get_logger()

def sqrt(num:float)->float:
  return np.sqrt(num)

@pyplugs.register
def sample_normal_distribution(
              random_seed: int = 0,
              mean: float = 0,
              var: float = 1,
              sample_size: int = 100)-> np.ndarray:
  if var<=0:
      LOGGER.warning(f"Variance {var} must be greater than 0 - defaulting to variance=1")
      var=1
  rng = np.random.default_rng(seed=random_seed)
  std_dev = sqrt(var)
  draws = rng.normal(loc=mean, scale=std_dev, size=sample_size)
  return draws


@pyplugs.register
def add_noise(input_array: np.ndarray,
              random_seed: int = 0,
              noise_type: str = 'normal', # Options: normal, uniform
              var:float = 1,
              mean:float = 0,
              )-> np.ndarray:
    rng = np.random.default_rng(random_seed)
    if var<=0:
        LOGGER.warning(f"Variance {var} must be greater than 0 - defaulting to variance=1")
        var=1
    if noise_type == "normal":
        std_dev = sqrt(var)
        noise = rng.normal(loc=mean, scale=std_dev, size=len(input_array))
    elif noise_type == "uniform":
        a = np.sqrt(3 * var)
        noise = rng.uniform(low=-a, high=a, size=len(input_array))
    else:
        raise ValueError(f"Unsupported noise_type: {noise_type}")

    return input_array + noise

@pyplugs.register
def nonlinear_transform(input_array: np.ndarray,
                        transform: str = "square") -> np.ndarray:

    if transform == "square":
        return input_array ** 2
    elif transform == "log":
        return np.log1p(input_array - np.min(input_array) + 1)
    elif transform == "tanh":
        return np.tanh(input_array)
    else:
        raise ValueError(f"Unsupported transform: {transform}")

@pyplugs.register
def print_stats(input_array: np.ndarray, plugin_step_name: str) -> None:
    arr_mean = float(np.mean(input_array))
    arr_std = float(np.std(input_array))
    arr_min = float(np.min(input_array))
    arr_max = float(np.max(input_array))
    arr_len = int(len(input_array))

    LOGGER.info(
        f"Plugin Task: '{plugin_step_name}' - "
        f"The mean value of the array after this step was {arr_mean:.4f}, "
        f"with std={arr_std:.4f}, min={arr_min:.4f}, max={arr_max:.4f}, len={arr_len}."

    )
    
# [new-plugin-definition]
import os

@pyplugs.register
def log_stats(input_array: np.ndarray, plugin_step_name: str) -> None:    
    arr_mean = float(np.mean(input_array))
    arr_std = float(np.std(input_array))
    arr_min = float(np.min(input_array))
    arr_max = float(np.max(input_array))
    arr_len = int(len(input_array))
    
    metrics = {
        "mean": arr_mean,
        "std": arr_std,
        "min": arr_min,
        f"max": arr_max,
        f"len": arr_len,
    }

    try:
        # Try and log metrics using Dioptra client 
        from dioptra.sdk.utilities.auth_client import get_authenticated_worker_client

        # Get the job ID and client
        job_id = os.environ["__JOB_ID"]
        dioptra_client = get_authenticated_worker_client(LOGGER, "json")

        for metric_name, value in metrics.items():
            dioptra_client.jobs.append_metric_by_id(
                job_id=job_id,
                metric_name=metric_name,
                metric_value=value, 
                metric_step=plugin_step_name,
            )

    # Handle failure and fall back to basic logging
    except Exception as e:
        LOGGER.warning(
            f"Failed to log metrics for '{plugin_step_name}' to Dioptra client, falling back to standard logger.",
            error=str(e)
        )
        
        LOGGER.info(
            f"Plugin Task: '{plugin_step_name}' - "
            f"The mean value of the array after this step was {arr_mean:.4f}, "
            f"with std={arr_std:.4f}, min={arr_min:.4f}, max={arr_max:.4f}, len={arr_len}."
        )