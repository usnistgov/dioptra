import numpy as np
import structlog
from dioptra import pyplugs

LOGGER = structlog.get_logger()

# Helper function - not registered as a Dioptra plugin task
def sqrt(num:float)->float:
  return np.sqrt(num)

@pyplugs.register
def sample_normal_distribution_print_mean(
              random_seed: int = 0,
              mean: float = 0,
              var: float = 1,
              sample_size: int = 100) -> np.ndarray :

  rng = np.random.default_rng(seed=random_seed)
  std_dev = sqrt(var)
  draws = rng.normal(loc=mean, scale=std_dev, size=sample_size)
  draws_mean = np.mean(draws)
  diff = np.abs(mean-draws_mean)
  pct = 100*diff/mean

  LOGGER.info(
      "Plugin 2 - "
      f"The mean value of the draws was {draws_mean:.4f}, "
      f"which was {diff:.4f} different from the passed-in mean ({pct:.2f}%). "
      "[Passed-in Parameters]"
      f"Seed: {random_seed}; "
      f"Mean: {mean}; "
      f"Variance: {var}; "
      f"Sample Size: {sample_size};"
      )

  return draws
