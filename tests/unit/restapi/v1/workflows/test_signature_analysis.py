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
from http import HTTPStatus
from pathlib import Path
from typing import Any

from flask_sqlalchemy import SQLAlchemy

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient

expected_outputs = {}

expected_outputs["sample_test_real_world.py"] = [
    {
        "name": "load_dataset",
        "inputs": [
            {"name": "ep_seed", "type": "integer", "required": False},
            {"name": "training_dir", "type": "string", "required": False},
            {"name": "testing_dir", "type": "string", "required": False},
            {"name": "subsets", "type": "list_str", "required": False},
            {"name": "image_size", "type": "tuple_int_int_int", "required": False},
            {"name": "rescale", "type": "number", "required": False},
            {"name": "validation_split", "type": "optional_float", "required": False},
            {"name": "batch_size", "type": "integer", "required": False},
            {"name": "label_mode", "type": "string", "required": False},
            {"name": "shuffle", "type": "boolean", "required": False},
        ],
        "outputs": [{"name": "output", "type": "directoryiterator"}],
        "missing_types": [
            {"name": "list_str", "description": "List[str]"},
            {
                "name": "tuple_int_int_int",
                "description": "Tuple[int, int, int]",
            },
            {"name": "optional_float", "description": "Optional[float]"},
            {"name": "directoryiterator", "description": "DirectoryIterator"},
        ],
    },
    {
        "name": "create_model",
        "inputs": [
            {"name": "dataset", "type": "directoryiterator", "required": False},
            {"name": "model_architecture", "type": "string", "required": False},
            {"name": "input_shape", "type": "tuple_int_int_int", "required": False},
            {"name": "loss", "type": "string", "required": False},
            {"name": "learning_rate", "type": "number", "required": False},
            {"name": "optimizer", "type": "string", "required": False},
            {"name": "metrics_list", "type": "list_dict_str_any", "required": False},
        ],
        "outputs": [],
        "missing_types": [
            {"name": "directoryiterator", "description": "DirectoryIterator"},
            {
                "name": "tuple_int_int_int",
                "description": "Tuple[int, int, int]",
            },
            {
                "name": "list_dict_str_any",
                "description": "List[Dict[str, Any]]",
            },
        ],
    },
    {
        "name": "load_model",
        "inputs": [
            {"name": "model_name", "type": "str_none", "required": False},
            {"name": "model_version", "type": "int_none", "required": False},
            {"name": "imagenet_preprocessing", "type": "boolean", "required": False},
            {"name": "art", "type": "boolean", "required": False},
            {"name": "image_size", "type": "any", "required": False},
            {
                "name": "classifier_kwargs",
                "type": "optional_dict_str_any",
                "required": False,
            },
        ],
        "outputs": [],
        "missing_types": [
            {"name": "str_none", "description": "str | None"},
            {"name": "int_none", "description": "int | None"},
            {
                "name": "optional_dict_str_any",
                "description": "Optional[Dict[str, Any]]",
            },
        ],
    },
    {
        "name": "train",
        "inputs": [
            {"name": "estimator", "type": "any", "required": True},
            {"name": "x", "type": "any", "required": False},
            {"name": "y", "type": "any", "required": False},
            {"name": "callbacks_list", "type": "list_dict_str_any", "required": False},
            {"name": "fit_kwargs", "type": "optional_dict_str_any", "required": False},
        ],
        "outputs": [],
        "missing_types": [
            {
                "name": "list_dict_str_any",
                "description": "List[Dict[str, Any]]",
            },
            {
                "name": "optional_dict_str_any",
                "description": "Optional[Dict[str, Any]]",
            },
        ],
    },
    {
        "name": "save_artifacts_and_models",
        "inputs": [
            {"name": "artifacts", "type": "list_dict_str_any", "required": False},
            {"name": "models", "type": "list_dict_str_any", "required": False},
        ],
        "outputs": [],
        "missing_types": [
            {
                "name": "list_dict_str_any",
                "description": "List[Dict[str, Any]]",
            }
        ],
    },
    {
        "name": "load_artifacts_for_job",
        "inputs": [
            {"name": "job_id", "type": "string", "required": True},
            {"name": "files", "type": "list_str_path", "required": False},
            {"name": "extract_files", "type": "list_str_path", "required": False},
        ],
        "outputs": [],
        "missing_types": [{"name": "list_str_path", "description": "List[str | Path]"}],
    },
    {
        "name": "load_artifacts",
        "inputs": [
            {"name": "artifact_ids", "type": "list_int", "required": False},
            {"name": "extract_files", "type": "list_str_path", "required": False},
        ],
        "outputs": [],
        "missing_types": [
            {"name": "list_int", "description": "List[int]"},
            {"name": "list_str_path", "description": "List[str | Path]"},
        ],
    },
    {
        "name": "attack_fgm",
        "inputs": [
            {"name": "dataset", "type": "any", "required": True},
            {"name": "adv_data_dir", "type": "union_str_path", "required": True},
            {"name": "classifier", "type": "any", "required": True},
            {"name": "distance_metrics", "type": "list_dict_str_str", "required": True},
            {"name": "batch_size", "type": "integer", "required": False},
            {"name": "eps", "type": "number", "required": False},
            {"name": "eps_step", "type": "number", "required": False},
            {"name": "minimal", "type": "boolean", "required": False},
            {"name": "norm", "type": "union_int_float_str", "required": False},
        ],
        "outputs": [],
        "missing_types": [
            {"name": "union_str_path", "description": "Union[str, Path]"},
            {
                "name": "list_dict_str_str",
                "description": "List[Dict[str, str]]",
            },
            {
                "name": "union_int_float_str",
                "description": "Union[int, float, str]",
            },
        ],
    },
    {
        "name": "attack_patch",
        "inputs": [
            {"name": "data_flow", "type": "any", "required": True},
            {"name": "adv_data_dir", "type": "union_str_path", "required": True},
            {"name": "model", "type": "any", "required": True},
            {"name": "patch_target", "type": "integer", "required": True},
            {"name": "num_patch", "type": "integer", "required": True},
            {"name": "num_patch_samples", "type": "integer", "required": True},
            {"name": "rotation_max", "type": "number", "required": True},
            {"name": "scale_min", "type": "number", "required": True},
            {"name": "scale_max", "type": "number", "required": True},
            {"name": "learning_rate", "type": "number", "required": True},
            {"name": "max_iter", "type": "integer", "required": True},
            {"name": "patch_shape", "type": "tuple", "required": True},
        ],
        "outputs": [],
        "missing_types": [
            {"name": "union_str_path", "description": "Union[str, Path]"},
            {"name": "tuple", "description": "Tuple"},
        ],
    },
    {
        "name": "augment_patch",
        "inputs": [
            {"name": "data_flow", "type": "any", "required": True},
            {"name": "adv_data_dir", "type": "union_str_path", "required": True},
            {"name": "patch_dir", "type": "union_str_path", "required": True},
            {"name": "model", "type": "any", "required": True},
            {"name": "patch_shape", "type": "tuple", "required": True},
            {"name": "distance_metrics", "type": "list_dict_str_str", "required": True},
            {"name": "batch_size", "type": "integer", "required": False},
            {"name": "patch_scale", "type": "number", "required": False},
            {"name": "rotation_max", "type": "number", "required": False},
            {"name": "scale_min", "type": "number", "required": False},
            {"name": "scale_max", "type": "number", "required": False},
        ],
        "outputs": [],
        "missing_types": [
            {"name": "union_str_path", "description": "Union[str, Path]"},
            {"name": "tuple", "description": "Tuple"},
            {
                "name": "list_dict_str_str",
                "description": "List[Dict[str, str]]",
            },
        ],
    },
    {
        "name": "model_metrics",
        "inputs": [
            {"name": "classifier", "type": "any", "required": True},
            {"name": "dataset", "type": "any", "required": True},
        ],
        "outputs": [],
        "missing_types": [],
    },
    {
        "name": "prediction_metrics",
        "inputs": [
            {"name": "y_true", "type": "np_ndarray", "required": True},
            {"name": "y_pred", "type": "np_ndarray", "required": True},
            {"name": "metrics_list", "type": "list_dict_str_str", "required": True},
            {"name": "func_kwargs", "type": "dict_str_dict_str_any", "required": False},
        ],
        "outputs": [],
        "missing_types": [
            {"name": "np_ndarray", "description": "np.ndarray"},
            {
                "name": "list_dict_str_str",
                "description": "List[Dict[str, str]]",
            },
            {
                "name": "dict_str_dict_str_any",
                "description": "Dict[str, Dict[str, Any]]",
            },
        ],
    },
    {
        "name": "augment_data",
        "inputs": [
            {"name": "dataset", "type": "any", "required": True},
            {"name": "def_data_dir", "type": "union_str_path", "required": True},
            {"name": "image_size", "type": "tuple_int_int_int", "required": True},
            {"name": "distance_metrics", "type": "list_dict_str_str", "required": True},
            {"name": "batch_size", "type": "integer", "required": False},
            {"name": "def_type", "type": "string", "required": False},
            {
                "name": "defense_kwargs",
                "type": "optional_dict_str_any",
                "required": False,
            },
        ],
        "outputs": [],
        "missing_types": [
            {"name": "union_str_path", "description": "Union[str, Path]"},
            {
                "name": "tuple_int_int_int",
                "description": "Tuple[int, int, int]",
            },
            {
                "name": "list_dict_str_str",
                "description": "List[Dict[str, str]]",
            },
            {
                "name": "optional_dict_str_any",
                "description": "Optional[Dict[str, Any]]",
            },
        ],
    },
    {
        "name": "predict",
        "inputs": [
            {"name": "classifier", "type": "any", "required": True},
            {"name": "dataset", "type": "any", "required": True},
            {"name": "show_actual", "type": "boolean", "required": False},
            {"name": "show_target", "type": "boolean", "required": False},
        ],
        "outputs": [],
        "missing_types": [],
    },
    {
        "name": "load_predictions",
        "inputs": [
            {"name": "paths", "type": "list_str", "required": True},
            {"name": "filename", "type": "string", "required": True},
            {"name": "format", "type": "string", "required": False},
            {"name": "dataset", "type": "directoryiterator", "required": False},
            {"name": "n_classes", "type": "integer", "required": False},
        ],
        "outputs": [],
        "missing_types": [
            {"name": "list_str", "description": "List[str]"},
            {"name": "directoryiterator", "description": "DirectoryIterator"},
        ],
    },
]

expected_outputs["sample_test_alias.py"] = [
    {"name": "test_plugin", "inputs": [], "outputs": [], "missing_types": []}
]

expected_outputs["sample_test_complex_type.py"] = [
    {
        "name": "the_plugin",
        "inputs": [
            {
                "name": "arg1",
                "type": "optional_str",
                "required": True,
            }
        ],
        "outputs": [{"name": "output", "type": "union_int_bool"}],
        "missing_types": [
            {"name": "optional_str", "description": "Optional[str]"},
            {"name": "union_int_bool", "description": "Union[int, bool]"},
        ],
    }
]

expected_outputs["sample_test_function_type.py"] = [
    {
        "name": "plugin_func",
        "inputs": [
            {
                "name": "arg1",
                "type": "type1",
                "required": True,
            }
        ],
        "outputs": [{"name": "output", "type": "type1"}],
        "missing_types": [
            {"name": "type1", "description": "foo(2)"},
        ],
    }
]

expected_outputs["sample_test_none_return.py"] = [
    {"name": "my_plugin", "inputs": [], "outputs": [], "missing_types": []}
]

expected_outputs["sample_test_optional.py"] = [
    {
        "name": "do_things",
        "inputs": [
            {
                "name": "arg1",
                "type": "optional_str",
                "required": True,
            },
            {
                "name": "arg2",
                "type": "integer",
                "required": False,
            },
        ],
        "outputs": [],
        "missing_types": [
            {"name": "optional_str", "description": "Optional[str]"},
        ],
    }
]

expected_outputs["sample_test_pyplugs_alias.py"] = [
    {"name": "test_plugin", "inputs": [], "outputs": [], "missing_types": []}
]

expected_outputs["sample_test_redefinition.py"] = [
    {"name": "test_plugin", "inputs": [], "outputs": [], "missing_types": []},
    {"name": "test_plugin2", "inputs": [], "outputs": [], "missing_types": []},
]

expected_outputs["sample_test_register_alias.py"] = [
    {"name": "test_plugin", "inputs": [], "outputs": [], "missing_types": []}
]

expected_outputs["sample_test_type_conflict.py"] = [
    {
        "name": "plugin_func",
        "inputs": [
            {
                "name": "arg1",
                "type": "type2",
                "required": True,
            },
            {
                "name": "arg2",
                "type": "type1",
                "required": True,
            },
        ],
        "outputs": [{"name": "output", "type": "type2"}],
        "missing_types": [
            {"name": "type2", "description": "foo(2)"},
            {"name": "type1", "description": "Type1"},
        ],
    }
]

# -- Assertions ------------------------------------------------------------------------


def assert_signature_analysis_response_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    """Assert that a job response contents is valid.

    Args:
        response: The actual response from the API.
        expected_contents: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response or if the response contents is not
            valid.
    """
    # Check expected keys
    expected_keys = {
        "name",
        "missing_types",
        "outputs",
        "inputs",
    }
    assert set(response.keys()) == expected_keys

    # Check basic response types
    assert isinstance(response["name"], str)
    assert isinstance(response["outputs"], list)
    assert isinstance(response["missing_types"], list)
    assert isinstance(response["inputs"], list)

    def sort_by_name(lst, k="name"):
        return sorted(lst, key=lambda x: x[k])

    assert sort_by_name(response["outputs"]) == sort_by_name(
        expected_contents["outputs"]
    )
    assert sort_by_name(response["inputs"]) == sort_by_name(expected_contents["inputs"])
    assert sort_by_name(response["missing_types"], k="name") == sort_by_name(
        expected_contents["missing_types"], k="name"
    )


def assert_signature_analysis_responses_matches_expectations(
    responses: list[dict[str, Any]], expected_contents: list[dict[str, Any]]
) -> None:
    assert len(responses) == len(expected_contents)
    for response in responses:
        assert_signature_analysis_response_matches_expectations(
            response, [a for a in expected_contents if a["name"] == response["name"]][0]
        )


def assert_signature_analysis_file_load_and_contents(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    filename: str,
):
    location = Path(__file__).absolute().parent / "signature_analysis" / filename

    with location.open("r") as f:
        contents = f.read()

    contents_analysis = dioptra_client.workflows.analyze_plugin_task_signatures(
        python_code=contents,
    )

    assert contents_analysis.status_code == HTTPStatus.OK

    assert_signature_analysis_responses_matches_expectations(
        contents_analysis.json()["tasks"],
        expected_contents=expected_outputs[filename],
    )


# -- Tests -----------------------------------------------------------------------------


def test_signature_analysis(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
) -> None:
    """
        Test that signature analysis
    Args:
        client: The Flask test client.
    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """

    for fn in expected_outputs:
        assert_signature_analysis_file_load_and_contents(
            dioptra_client=dioptra_client, filename=fn
        )
