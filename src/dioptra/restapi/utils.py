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
"""A module of utility functions that are used across multiple endpoints.

.. |Namespace| replace:: :py:class:`~flask_restx.Namespace`
.. |ParametersSchema| replace:: :py:class:`~.ParametersSchema`
.. |RequestParser| replace:: :py:class:`~flask_restx.reqparse.RequestParser`
.. |Resource| replace:: :py:class:`~flask_restx.Resource`
"""
from __future__ import annotations

import datetime
import functools
from importlib.resources import as_file, files
from typing import Any, Callable, List, Protocol, Type, cast

from flask.views import View
from flask_restx import Api, Namespace, Resource, inputs
from flask_restx.reqparse import RequestParser
from injector import Injector
from marshmallow import Schema
from marshmallow import fields as ma
from marshmallow import missing
from marshmallow.schema import SchemaMeta
from typing_extensions import TypedDict
from werkzeug.datastructures import FileStorage

from dioptra.restapi.v1.shared.request_scope import set_request_scope_callbacks

from .custom_schema_fields import FileUpload


class ParametersSchema(TypedDict, total=False):
    """A schema of the parameters that can be passed to the |RequestParser|."""

    name: str
    type: object
    location: str
    required: bool
    default: Any | None
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


def as_parameters_schema_list(
    schema: Schema | SchemaMeta, operation: str, location: str
) -> list[ParametersSchema]:
    """Converts a Marshmallow Schema into a list of ParametersSchema dictionaries.

    This primary use case for this function is for converting a Marshmallow Schema into
    a format that can passed to the `as_api_parser` utility function so that the Swagger
    documentation is correct.

    Args:
        schema: A Marshmallow Schema or SchemaMeta object.
        operation: The Schema operation the REST API is going to perform. Use "load"
            for a request and "dump" for a response.
        location: The location where the request or response parameters are stored.
            Must be either "args", "form", or "json".

    Returns:
        A list of ParametersSchema dictionaries.

    Raises:
        ValueError: If `operation` is not "dump" or "load".

    Note:
        This is a necessary workaround because the @accepts decorator ignores the
        load_only and dump_only settings on a Marshmallow Schema that's passed to the
        form_schema= argument when generating the Swagger documentation.
    """
    if operation not in {"dump", "load"}:
        raise ValueError(f"Invalid operation: {operation}. Must be 'dump' or 'load'")

    if isinstance(schema, SchemaMeta):
        schema = cast(Schema, schema())

    parameters_schema_list: list[ParametersSchema] = []
    for field in schema.fields.values():
        if operation == "dump" and not field.load_only:
            parameters_schema_list.append(
                create_parameters_schema(field, operation, location)
            )

        if operation == "load" and not field.dump_only:
            parameters_schema_list.append(
                create_parameters_schema(field, operation, location)
            )

    return parameters_schema_list


def create_parameters_schema(
    field: ma.Field, operation: str, location: str
) -> ParametersSchema:
    """Converts a Marshmallow Field into a ParametersSchema dictionary.

    Args:
        field: A Marshmallow Field object.
        operation: The Schema operation the REST API is going to perform. Use "load"
            for a request and "dump" for a response.
        location: The location where the request or response parameters are stored.
            Must be either "args", "form", or "json".

    Returns:
        A ParametersSchema dictionary.
    """
    parameter_type = TYPE_MAP_MA_TO_REQPARSE[type(field)]

    if parameter_type is FileStorage:
        location = "files"

    parameters_schema = ParametersSchema(
        name=cast(str, field.name),
        type=parameter_type,
        location=location,
        required=field.required,
    )

    if operation == "load" and field.load_default is not missing:
        parameters_schema["default"] = field.load_default

    if operation == "dump" and field.dump_default is not missing:
        parameters_schema["default"] = field.dump_default

    if field.metadata.get("description") is not None:
        parameters_schema["help"] = field.metadata["description"]

    return parameters_schema


def slugify(text: str) -> str:
    """Slugify a string.

    A "slugified" string is a string that has been lowercased and had all of its
    spaces replaced with hyphens.

    Args:
        text: The text to slugifiy.

    Returns:
        A slugified string
    """

    return text.lower().strip().replace(" ", "-")


def read_text_file(package: str, filename: str) -> str:
    """Read a text file from a specified package into a string.

    Args:
        package: The name of the Python package containing the text file. This should
            be a string representing the package's import path, for example
            "my_package.subpackage".
        filename: The base name of the text file, including its extension. For
            example, "data.txt".

    Returns:
        A string with the contents of the text file.
    """
    traversable = files(package).joinpath(filename)
    with as_file(traversable) as fp:
        return fp.read_text()


class _ClassBasedViewFunction(Protocol):
    """
    We distinguish a class-based view function from other view functions
    by looking for a "view_class" attribute on the function.
    """

    view_class: Type[View]

    def __call__(self, *args, **kwargs) -> Any: ...  # noqa: E704


def _new_class_view_function(
    func: _ClassBasedViewFunction, injector: Injector, api: Api
) -> Callable[..., Any]:
    """
    Create a view function which supports injection, based on the given
    class-based view function.  "Wrapping" func won't work here, in the sense
    that our view function can't delegate to func since the latter does not
    support dependency-injected view object creation.  So we create a brand new
    one (@wrap'd, so it has the look of func at least), which does
    dependency-injected view creation.

    Args:
        func: The old class-based view function
        injector: An injector
        api: The flask_restx Api instance

    Returns:
        A new view function
    """

    is_restx_resource = issubclass(func.view_class, Resource)

    additional_kwargs = {}
    if is_restx_resource:
        additional_kwargs["api"] = api

    # Honoring init_every_request is simple enough to do, so why not.
    # It was added in Flask 2.2.0; it behaved as though True, previously.
    init_every_request = getattr(func.view_class, "init_every_request", True)

    if not init_every_request:
        view_obj = injector.create_object(
            func.view_class, additional_kwargs=additional_kwargs
        )

    @functools.wraps(
        func,
        assigned=functools.WRAPPER_ASSIGNMENTS
        + ("view_class", "methods", "provide_automatic_options"),
    )
    def new_view_func(*args, **kwargs):
        nonlocal view_obj
        if init_every_request:
            view_obj = injector.create_object(
                func.view_class, additional_kwargs=additional_kwargs
            )

        return view_obj.dispatch_request(*args, **kwargs)

    if is_restx_resource:
        new_view_func = api.output(new_view_func)

    return new_view_func


def setup_injection(api: Api, injector: Injector) -> None:
    """
    Fixup the given flask app such that class-based view functions support
    dependency injection.

    Args:
        api: A flask_restx Api object.  This contains the flask app, and is
            also necessary to make restx views (resources) work with
            dependency injection.
        injector: An injector
    """

    new_view_func: Callable[..., Any]

    for key, func in api.app.view_functions.items():
        if hasattr(func, "view_class"):
            new_view_func = _new_class_view_function(func, injector, api)
            api.app.view_functions[key] = new_view_func

    set_request_scope_callbacks(api.app, injector)

    # Uncomment to see more detailed logging regarding dependency injection
    # in debug mode.
    # if api.app.debug:
    #     injector_logger = logging.getLogger("injector")
    #     injector_logger.setLevel(logging.DEBUG)


TYPE_MAP_MA_TO_REQPARSE = {
    ma.AwareDateTime: str,
    ma.Bool: inputs.boolean,
    ma.Boolean: inputs.boolean,
    ma.Constant: str,
    ma.Date: inputs.date_from_iso8601,
    ma.DateTime: inputs.datetime_from_iso8601,
    ma.Decimal: float,
    ma.Dict: dict,
    ma.Email: str,
    FileUpload: FileStorage,
    ma.Float: float,
    ma.Function: str,
    ma.Int: int,
    ma.Integer: int,
    ma.Length: float,
    ma.List: list,
    ma.Mapping: dict,
    ma.Method: str,
    ma.NaiveDateTime: inputs.datetime_from_iso8601,
    ma.Number: float,
    ma.Pluck: str,
    ma.Raw: str,
    ma.Str: str,
    ma.String: str,
    ma.Time: datetime.time.fromisoformat,
    ma.Url: str,
    ma.URL: str,
    ma.UUID: str,
}
