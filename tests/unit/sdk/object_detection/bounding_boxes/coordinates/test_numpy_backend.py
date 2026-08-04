# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
import importlib.util
import sys
import types
from pathlib import Path

import numpy as np
import pytest

# Import numpy_backend by file path so the test does not pull in the
# coordinates package __init__ (which imports the heavy tensorflow backend).
_COORDS_DIR = (
    Path(__file__).resolve().parents[6]
    / "src"
    / "dioptra"
    / "sdk"
    / "object_detection"
    / "bounding_boxes"
    / "coordinates"
)


def _load_numpy_backend():
    pkg_name = "_dioptra_coords_test_pkg"
    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(_COORDS_DIR)]
        sys.modules[pkg_name] = pkg

    def _load(modname, filename):
        full = f"{pkg_name}.{modname}"
        if full in sys.modules:
            return sys.modules[full]
        spec = importlib.util.spec_from_file_location(full, _COORDS_DIR / filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules[full] = module
        spec.loader.exec_module(module)
        return module

    _load("bounding_box_coordinates", "bounding_box_coordinates.py")
    return _load("numpy_backend", "numpy_backend.py")


numpy_backend = _load_numpy_backend()
NumpyBoundingBoxCoordinates = numpy_backend.NumpyBoundingBoxCoordinates


@pytest.mark.parametrize("grid_shape", [(7, 7), (13, 13), (5, 9)])
@pytest.mark.parametrize("center", [1.0, 1.25, 2.0])
def test_find_bbox_cell_ij_edge_center_is_in_bounds(grid_shape, center) -> None:
    """A bounding-box center on or past the far image edge must be clamped to a
    valid cell index (0 .. n-1), never to the out-of-range index n."""
    coords = NumpyBoundingBoxCoordinates(grid_shape=grid_shape)

    cell_ij = coords.find_bbox_cell_ij(
        x_center=np.array([center], dtype="float64"),
        y_center=np.array([center], dtype="float64"),
    )

    i = int(cell_ij[0][0])
    j = int(cell_ij[0][1])

    assert 0 <= i <= coords.cell_nrow - 1
    assert 0 <= j <= coords.cell_ncol - 1
    # The far-edge center belongs in the last cell.
    assert i == coords.cell_nrow - 1
    assert j == coords.cell_ncol - 1


def test_find_bbox_cell_ij_index_usable_as_grid_index() -> None:
    """The returned indices must be valid indices into a (nrow, ncol, ...) grid,
    exactly as NumpyBoundingBoxesBatchedGrid.embed() uses them."""
    coords = NumpyBoundingBoxCoordinates(grid_shape=(7, 7))
    cell_ij = coords.find_bbox_cell_ij(
        x_center=np.array([1.0], dtype="float64"),
        y_center=np.array([1.0], dtype="float64"),
    )

    grid = np.zeros((coords.cell_nrow, coords.cell_ncol, 4), dtype="float32")
    grid_i = np.transpose(cell_ij)[0]
    grid_j = np.transpose(cell_ij)[1]

    # Must not raise IndexError.
    grid[grid_i, grid_j] = np.array([0.0, 0.0, 0.0, 0.0], dtype="float32")
