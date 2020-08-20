from flask import Flask
from flask_restx import Api

BASE_ROUTE: str = "job"


def register_routes(api: Api, app: Flask, root: str = "api") -> None:
    from .controller import api as endpoint_api

    api.add_namespace(endpoint_api, path=f"/{root}/{BASE_ROUTE}")
