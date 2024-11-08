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

"""Utility functions for plugin modules"""


from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union


def ensure_list(string: List | str) -> List:
    """Utility: coerces a string into a list."""
    if isinstance(string, str):
        return [string]
    elif isinstance(string, list):
        return string
    else:
        raise ValueError


def get_dict_value(data_dict, key, error_type="KeyError", error_message=None):
    """Tries to fetch value from dict and throws error if missing"""
    if key in data_dict:
        return data_dict[key]
    else:
        error_message = (
            error_message or f"The key '{key}' was not found in the dictionary."
        )

    if error_type == "KeyError":
        raise KeyError(error_message)
    elif error_type == "ValueError":
        raise ValueError(error_message)
    else:
        raise Exception("Unsupported error type specified")
