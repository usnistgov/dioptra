from dioptra import pyplugs
import numpy as np

@pyplugs.register
def sample_function(a: np.ndarray, b: str) -> str:
    return f"{b}: {a}"
