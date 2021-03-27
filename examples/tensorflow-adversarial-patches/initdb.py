#!/usr/bin/env python

from flask import Flask
from flask_migrate import stamp

from mitre.securingai.restapi import create_app
from mitre.securingai.restapi.app import db

app: Flask = create_app(env="prod")

with app.app_context():
    db.create_all()
    db.session.commit()
    stamp()
