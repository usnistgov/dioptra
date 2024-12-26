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
import requests
import structlog
import os
from dioptra import pyplugs
from dioptra.client import connect_json_dioptra_client
from structlog.stdlib import BoundLogger
from posixpath import join as urljoin
from urllib.parse import urlparse, urlunparse

LOGGER: BoundLogger = structlog.stdlib.get_logger()

@pyplugs.register    
def get_uri_for_model(model_name, model_version=-1):
    session, url = get_logged_in_session()
    models = get(session, url, f'models?search={model_name}&pageLength=500')
    for model in models['data']:
        if (model['name'] == model_name):
            model_id = model['id']
            if (model_version >= 0):
                selected_model = get(session, url, 
                    f'models/{model_id}/versions/{model_version}'
                )
            else:
                selected_model = model['latestVersion']

    uri = selected_model['artifact']['artifactUri']
    return uri

def get_uris_for_job(job_id):
    session, url = get_logged_in_session()
    job = get(session, url, 'jobs', str(job_id))
    return [artifact['artifactUri'] for artifact in job['artifacts']]

def get_uris_for_artifacts(artifact_ids):
    session, url = get_logged_in_session()
    return [get(session, url, 'artifacts', aid) for aid in artifact_ids]

def get_logged_in_session():
    session = requests.Session()
    url = "http://dioptra-deployment-restapi:5000/api/v1"

    login = post(session, url, {
            'username':os.environ['DIOPTRA_WORKER_USERNAME'], 
            'password':os.environ['DIOPTRA_WORKER_PASSWORD']},
            'auth', 'login')
    LOGGER.info("login request sent", response=str(login))

    return session, url

def upload_model_to_restapi(name, source_uri, job_id):
    version = 0
    model_id = 0
    
    session, url = get_logged_in_session()

    models = get(session, url, f'models?search={name}&pageLength=500')
    LOGGER.info("requesting models from RESTAPI", response=models)

    
    for model in models['data']:
        #check whether to create a new model
        if model['name'] == name:
            model_id = model['id']
            if model['latestVersion'] != None:
                version = model['latestVersion']['versionNumber'] + 1
    if (version == 0 and model_id == 0):
        LOGGER.info("creating new model on RESTAPI")
        model = post(session, url, {"group": 1, "name": name, "description": f"{name} model"}, "models")
        model_id = model['id']
        LOGGER.info("new model created", response=model)
    
    artifact = post(session, url, {"group": 1, "description": f"{name} model artifact", "job": str(job_id), "uri": source_uri}, 'artifacts')
    LOGGER.info("artifact", response=artifact)
    model_version = post(session, url, {"description": f"{name} model version", "artifact": artifact['id']}, 'models', str(model_id), 'versions')
    LOGGER.info("model created", response=model_version)

def upload_artifact_to_restapi(source_uri, job_id):
    session, url = get_logged_in_session()

    artifact = post(session, url, {"group": 1, "description": f"artifact for job {job_id}", "job": str(job_id), "uri": source_uri}, 'artifacts')
    LOGGER.info("artifact", response=artifact)

def debug_request(url, method, data=None):
    LOGGER.debug("Request made.", url=url, method=method, data=data)


def debug_response(json):
    LOGGER.debug("Response received.", json=json)


def get(session, endpoint, *features):
    debug_request(urljoin(endpoint, *features), "GET")
    return make_request(session, "get", endpoint, None, *features)


def post(session, endpoint, data, *features):
    debug_request(urljoin(endpoint, *features), "POST", data)
    return make_request(session, "post", endpoint, data, *features)


def delete(session, endpoint, data, *features):
    debug_request(urljoin(endpoint, *features), "DELETE", data)
    return make_request(session, "delete", endpoint, data, *features)


def put(session, endpoint, data, *features):
    debug_request(urljoin(endpoint, *features), "PUT", data)
    return make_request(session, "put", endpoint, data, *features)


def make_request(session, method_name, endpoint, data, *features):
    url = urljoin(endpoint, *features)
    method = getattr(session, method_name)
    try:
        if data:
            response = method(url, json=data)
        else:
            response = method(url)
        if response.status_code != 200:
            raise StatusCodeError()
        json = response.json()
    except (requests.ConnectionError, StatusCodeError, requests.JSONDecodeError) as e:
        handle_error(session, url, method_name.upper(), data, response, e)
    debug_response(json=json)
    return json


def handle_error(session, url, method, data, response, error):
    if type(error) is requests.ConnectionError:
        restapi = os.environ["DIOPTRA_RESTAPI_URI"]
        message = (
            f"Could not connect to the REST API. Is the server running at {restapi}?"
        )
        LOGGER.error(message, url=url, method=method, data=data, response=response.text)
        raise APIConnectionError(message)
    if type(error) is StatusCodeError:
        message = f"Error code {response.status_code} returned."
        LOGGER.error(message, url=url, method=method, data=data, response=response.text)
        raise StatusCodeError(message)
    if type(error) is requests.JSONDecodeError:
        message = "JSON response could not be decoded."
        LOGGER.error(message, url=url, method=method, data=data, response=response.text)
        raise JSONDecodeError(message)

class APIConnectionError(Exception):
    """Class for connection errors"""


class StatusCodeError(Exception):
    """Class for status code errors"""


class JSONDecodeError(Exception):
    """Class for JSON decode errors"""
