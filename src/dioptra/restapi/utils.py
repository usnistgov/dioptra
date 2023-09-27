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

import functools
from typing import Any, Callable, List, Protocol, Type

from flask.views import View
from flask_restx import Api, Namespace, Resource
from flask_restx.reqparse import RequestParser
from injector import Injector
from typing_extensions import TypedDict

from dioptra.restapi.shared.request_scope import set_request_scope_callbacks


class ParametersSchema(TypedDict, total=False):
    """A schema of the parameters that can be passed to the |RequestParser|."""

    name: str
    type: object
    location: str
    required: bool
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


class _ClassBasedViewFunction(Protocol):
    """
    We distinguish a class-based view function from other view functions
    by looking for a "view_class" attribute on the function.
    """

    view_class: Type[View]

    def __call__(self, *args, **kwargs) -> Any:
        ...


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
