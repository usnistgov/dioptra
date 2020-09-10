import os

from mitre.securingai.restapi import create_app

app = create_app(env=os.getenv("AI_RESTAPI_ENV"))
