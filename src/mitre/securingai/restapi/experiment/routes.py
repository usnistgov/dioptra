# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""Methods for registering the experiment endpoint routes with the main application.

.. |Api| replace:: :py:class:`flask_restx.Api`
.. |Flask| replace:: :py:class:`flask.Flask`
"""

from flask import Flask
from flask_restx import Api

BASE_ROUTE: str = "experiment"


def register_routes(api: Api, app: Flask, root: str = "api") -> None:
    """Registers the experiment endpoint routes with the main application.

    Args:
        api: The main REST |Api| object.
        app: The main |Flask| application.
        root: The root path for the registration prefix of the namespace. The default
            is `"api"`.
    """
    from .controller import api as endpoint_api

    api.add_namespace(endpoint_api, path=f"/{root}/{BASE_ROUTE}")
