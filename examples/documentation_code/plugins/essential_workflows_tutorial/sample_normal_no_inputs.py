import numpy as np
import structlog

from dioptra import pyplugs

LOGGER = structlog.get_logger()

@pyplugs.register
def sample_normal_distribution_print_mean():

  rng = np.random.default_rng(seed=1)
  draws = rng.normal(loc=0, scale=1, size=100)
  LOGGER.info(
      "Plugin 1 - "
      "We took 100 draws from a normal distribution with mean 0 and variance 1."
      f" The mean value of the draws was {np.mean(draws):.4f}"
    )
