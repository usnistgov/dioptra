# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""A module of utility functions that are used across multiple endpoints.

.. |Namespace| replace:: :py:class:`~flask_restx.Namespace`
.. |ParametersSchema| replace:: :py:class:`~.ParametersSchema`
.. |RequestParser| replace:: :py:class:`~flask_restx.reqparse.RequestParser`
.. |Resource| replace:: :py:class:`~flask_restx.Resource`
"""

from typing import List

from flask_restx import Namespace
from flask_restx.reqparse import RequestParser
from typing_extensions import TypedDict


class ParametersSchema(TypedDict, total=False):
    """A schema of the parameters that can be passed to the |RequestParser|."""

    name: str
    type: object
    location: str
    help: str


def as_api_parser(
    api: Namespace, parameters_schema: List[ParametersSchema]
) -> RequestParser:
    """Creates a |RequestParser| from a list of |ParametersSchema| dictionaries.

    The primary use case for this utility function is to convert a submission form
    schema so that it can be passed to an `@api.expects` decorator and populate the
    form's fields in the Swagger documentation.

    Args:
        api: An endpoint's |Namespace| used for grouping |Resource|s.
        parameters_schema: A list of |ParametersSchema| dictionaries to add as arguments
            to `api.parser()`.

    Returns:
        A |RequestParser| object.
    """
    parser: RequestParser = api.parser()

    for form_kwargs in parameters_schema:
        parser.add_argument(**form_kwargs)

    return parser
