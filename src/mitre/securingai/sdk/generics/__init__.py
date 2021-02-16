from __future__ import annotations

from ._estimator_predict import estimator_predict
from ._fit_estimator import fit_estimator
from ._registry import register_entrypoints

__all__ = ["estimator_predict", "fit_estimator"]


register_entrypoints()
