#!/usr/bin/env python

import flask_migrate
from flask import Flask

from mitre.securingai.restapi import create_app

app: Flask = create_app(env="prod")

with app.app_context():
    flask_migrate.upgrade()
