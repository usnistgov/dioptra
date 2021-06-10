#!/usr/bin/env python
# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.

import flask_migrate
from flask import Flask

from mitre.securingai.restapi import create_app

app: Flask = create_app(env="prod")

with app.app_context():
    flask_migrate.upgrade()
