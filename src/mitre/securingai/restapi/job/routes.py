"""Methods for registering the job endpoint routes with the main application.

.. |Api| replace:: :py:class:`flask_restx.Api`
.. |Flask| replace:: :py:class:`flask.Flask`
"""

from flask import Flask
from flask_restx import Api

BASE_ROUTE: str = "job"


def register_routes(api: Api, app: Flask, root: str = "api") -> None:
    """Registers the job endpoint routes with the main application.

    Args:
        api: The main REST |Api| object.
        app: The main |Flask| application.
        root: The root path for the registration prefix of the namespace. The default
            is `"api"`.
    """
    from .controller import api as endpoint_api

    api.add_namespace(endpoint_api, path=f"/{root}/{BASE_ROUTE}")
