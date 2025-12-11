import matplotlib.pyplot as plt
import numpy as np
import structlog

from dioptra import pyplugs

LOGGER = structlog.get_logger()

def _as_1d_float_array(arr) -> np.ndarray:
    a = np.asarray(arr, dtype=float).ravel()
    if a.size == 0:
        raise ValueError("input_array is empty.")
    return a

@pyplugs.register
def scale_array(
    input_array: np.ndarray,
) -> dict:
    """Return a dict of rescaled arrays using z-score, min-max, and log1p methods."""\

    x = _as_1d_float_array(input_array)
    out = {}

    # Z-score scaling
    mu, sigma = np.mean(x), np.std(x)
    if sigma == 0.0:
        out["zscore"] = np.zeros_like(x)
    else:
        out["zscore"] = (x - mu) / sigma

    # Min-max scaling (to [0, 1])
    xmin, xmax = np.min(x), np.max(x)
    if xmax == xmin:
        out["minmax"] = np.full_like(x, 0.5)
    else:
        out["minmax"] = (x - xmin) / (xmax - xmin)

    # Log1p scaling (nonlinear, requires non-negative values)
    if np.any(x < 0):
        LOGGER.warn("scale_array_dict.log1p_negative", msg="Negative values present; log1p not applied.")
    else:
        out["log1p"] = np.log1p(x)

    return out

@pyplugs.register
def visualize_rescaling_multi(
    original_array: np.ndarray,
    rescaled_dict: dict,
    title: str = "Original vs Multiple Rescalings",
):
    """Compare multiple rescaling methods with scatterplots and stats."""\

    x = _as_1d_float_array(original_array)

    # Reorder dict to put minmax first if present
    methods = list(rescaled_dict.keys())
    if "minmax" in methods:
        methods = ["minmax"] + [m for m in methods if m != "minmax"]

    # Compute global y-limits across all rescaled arrays
    all_y = np.concatenate([_as_1d_float_array(rescaled_dict[m]) for m in methods])
    y_min = np.min(all_y)
    y_max = np.max(all_y)
    y_lim = (y_min, 1.1 * y_max)

    n_methods = len(methods)
    fig, axes = plt.subplots(1, n_methods, figsize=(5 * n_methods, 5), sharex=False, sharey=False)

    if n_methods == 1:
        axes = [axes]  # make iterable

    for ax, method in zip(axes, methods):
        y = rescaled_dict[method]
        # Truncate to shared length
        n = int(min(x.size, y.size))
        x_plot, y_plot = x[:n], y[:n]

        # Regression fit
        coef = np.polyfit(x_plot, y_plot, deg=1)
        slope, intercept = coef
        xx = np.linspace(np.min(x_plot), np.max(x_plot), 200)
        yy = np.polyval(coef, xx)

        # Scatter + regression
        ax.scatter(x_plot, y_plot, s=12, alpha=0.6, label="data")
        ax.plot(xx, yy, color="black", lw=1.2, label="regression")

        # Stats
        stats = f"""n_obs: {n}
min: {np.min(x_plot):.2f} → {np.min(y_plot):.2f}
max: {np.max(x_plot):.2f} → {np.max(y_plot):.2f}
mean: {np.mean(x_plot):.2f} → {np.mean(y_plot):.2f}
median: {np.median(x_plot):.2f} → {np.median(y_plot):.2f}
std dev: {np.std(x_plot):.2f} → {np.std(y_plot):.2f}
regression: y = {slope:.3f}·x + {intercept:.3f}""".strip()

        ax.set_xlabel("Original")
        ax.set_ylabel(method)
        ax.set_title(method)
        ax.set_ylim(y_lim)  # unified y-limits
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc="upper left")
        ax.text(
            0.98, 0.02, stats,
            transform=ax.transAxes,
            va="bottom", ha="right", fontsize=8,
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none")
        )

    fig.suptitle(title)
    fig.tight_layout()

    try:
        return fig
    finally:
        plt.close(fig)
