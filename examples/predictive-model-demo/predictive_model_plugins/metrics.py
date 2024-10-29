from __future__ import annotations

import numpy as np

def calc_MSE(
        y_true: np.ndarray,
        y_pred: np.ndarray
) -> float:
    
    return float(np.mean((y_true - y_pred)**2))