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
from __future__ import annotations

import os
from posixpath import join as urljoin
from urllib.parse import urlparse, urlunparse

import requests
import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class APIConnectionError(Exception):
    """Class for connection errors"""


class StatusCodeError(Exception):
    """Class for status code errors"""


class JSONDecodeError(Exception):
    """Class for JSON decode errors"""


def create_data_dict(**kwargs):
    return kwargs


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


class DioptraClient(object):
    def __init__(self, session=None, address=None, api_version="v1"):
        address = (
            f"{address}/api/{api_version}"
            if address
            else f"{os.environ['DIOPTRA_RESTAPI_URI']}/api/{api_version}"
        )

        self._session = session if session is not None else requests.Session()
        self._users = UsersClient(session, "users", address, api_version)
        self._auth = AuthClient(session, "auth", address, api_version)
        self._queues = QueuesClient(session, "queues", address, api_version)
        self._groups = GroupsClient(session, "groups", address, api_version)
        self._tags = TagsClient(session, "tags", address, api_version)
        self._plugins = PluginsClient(session, "plugins", address, api_version)
        self._pluginParameterTypes = PluginParameterTypesClient(
            session, "pluginParameterTypes", address, api_version
        )
        self._experiments = ExperimentsClient(
            session, "experiments", address, api_version
        )
        self._jobs = JobsClient(session, "jobs", address, api_version)
        self._entrypoints = EntrypointsClient(
            session, "entrypoints", address, api_version
        )
        # models
        # artifacts

    @property
    def users(self):
        return self.get_endpoint(self._users)

    @property
    def auth(self):
        return self.get_endpoint(self._auth)

    @property
    def queues(self):
        return self.get_endpoint(self._queues)

    @property
    def groups(self):
        return self.get_endpoint(self._groups)

    @property
    def tags(self):
        return self.get_endpoint(self._tags)

    @property
    def plugins(self):
        return self.get_endpoint(self._plugins)

    @property
    def pluginParameterTypes(self):
        return self.get_endpoint(self._pluginParameterTypes)

    @property
    def experiments(self):
        return self.get_endpoint(self._experiments)

    @property
    def jobs(self):
        return self.get_endpoint(self._jobs)

    @property
    def entrypoints(self):
        return self.get_endpoint(self._entrypoints)

    def get_endpoint(self, ep):
        ep.session = self._session
        return ep


class Endpoint(object):
    def __init__(self, session, ep_name, address, api_version):
        self._scheme, self._netloc, self._path, _, _, _ = urlparse(address)
        self._ep_name = ep_name
        self._session = session

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, s):
        self._session = s

    @property
    def url(self):
        return self.def_endpoint(self._ep_name)

    def def_endpoint(self, name):
        """creates base url for an endpoint by name"""
        return urlunparse(
            (self._scheme, self._netloc, urljoin(self._path, name + "/"), "", "", "")
        )


class HasTagsProvider(object):
    def __init__(self, url, session):
        self._tags = TagsProvider(url, session)

    @property
    def tags(self):
        return self.get_endpoint(self._tags)

    def get_endpoint(self, ep):
        ep.session = self._session
        return ep


class TagsProvider(object):
    def __init__(self, base_url, session):
        self.url = base_url
        self.session = session

    def get(self, parent_id):
        return get(self.session, self.url, str(parent_id), "tags")

    def modify(self, parent_id, ids):
        d = {"ids": ids}
        return put(self.session, self.url, d, str(parent_id), "tags")

    def delete_all(self, parent_id):
        d = None
        return delete(self.session, self.url, d, str(parent_id), "tags")

    def add(self, parent_id, ids):
        d = {"ids": ids}
        return post(self.session, self.url, d, str(parent_id), "tags")

    def delete(self, parent_id, tag_id):
        d = None
        return delete(self.session, self.url, d, str(parent_id), "tags", str(tag_id))


class UsersClient(Endpoint):
    def get_all(self):
        """gets all users"""
        return get(self.session, self.url)

    def create(self, username, email, password, confirm_password):
        """creates a user"""
        d = {
            "username": username,
            "email": email,
            "password": password,
            "confirmPassword": confirm_password,
        }
        return post(self.session, self.url, d)

    def get_by_id(self, user_id):
        """get a user by id"""
        return get(self.session, self.url, str(user_id))

    def update_password_by_id(
        self, user_id, old_password, new_password, confirm_new_password
    ):
        """change a user's password by id"""
        d = {
            "oldPassword": old_password,
            "newPassword": new_password,
            "confirmNewPassword": confirm_new_password,
        }
        return post(self.session, self.url, d, str(user_id), "password")

    def current(self):
        """get the current user"""
        return get(self.session, self.url, "current")

    def delete_current(self, password):
        """delete the current user"""
        d = {"password": password}
        return delete(self.session, self.url, d, "current")

    def modify_current(self, username, email):
        """modify the current user"""
        d = {"username": username, "email": email}
        return put(self.session, self.url, d, "current")

    def modify_current_password(self, old_password, new_password, confirm_new_password):
        """modify the current user's password"""
        d = {
            "oldPassword": old_password,
            "newPassword": new_password,
            "confirmNewPassword": confirm_new_password,
        }
        return post(self.session, self.url, d, "current", "password")

    def failed_user_post(self):
        """create a post request with an invalid schema, for testing"""
        return post(self.session, self.url, {"a": "doesnotexist"})

    def failed_user_get(self):
        """create a get request to an invalid url, for testing"""
        return get(self.session, self.url, "doesnotexist")


class AuthClient(Endpoint):
    def login(self, username, password):
        """login as the given user"""
        d = {"username": username, "password": password}
        return post(self.session, self.url, d, "login")

    def logout(self, everywhere):
        """logout as the current user"""
        d = {"everywhere": everywhere}
        return post(self.session, self.url, d, "logout")


class GroupsClient(Endpoint):
    def get_all(self):
        """get all groups"""
        return get(self.session, self.url)

    def get_by_id(self, gid):
        """get a group by id"""
        return get(self.session, self.url, str(gid))


class QueuesClient(Endpoint):
    def get_all(self):
        """gets all queues"""
        return get(self.session, self.url)

    def create(self, group, name, description):
        """create a queue"""
        d = {"group": group, "name": name, "description": description}
        return post(self.session, self.url, d)

    def get_drafts(self):
        """gets all queue drafts"""
        return get(self.session, self.url, "drafts")

    def create_draft(self, group, name, description):
        """create a draft"""
        d = {"group": group, "name": name, "description": description}
        return post(self.session, self.url, d, "drafts")

    def modify_draft_by_draft_id(self, draft_id, name, description):
        """modify a draft by id"""
        d = {"name": name, "description": description}
        return put(self.session, self.url, d, "drafts", str(draft_id))

    def delete_draft_by_draft_id(self, draft_id):
        """delete a draft by id"""
        d = None
        return delete(self.session, self.url, d, "drafts", str(draft_id))

    def get_draft_by_draft_id(self, draft_id):
        """get a draft by id"""
        return get(self.session, self.url, "drafts", str(draft_id))

    def modify_by_id(self, queue_id, name, description):
        """modify a queue by id"""
        d = {"name": name, "description": description}
        return put(self.session, self.url, d, str(queue_id))

    def delete_by_id(self, queue_id):
        """delete a queue by id"""
        d = None
        return delete(self.session, self.url, d, str(queue_id))

    def get_by_id(self, queue_id):
        """get a queue by id"""
        return get(self.session, self.url, str(queue_id))

    def modify_draft_by_queue_id(self, queue_id, name, description):
        """modify a draft by queue id"""
        d = {"name": name, "description": description}
        return put(self.session, self.url, d, str(queue_id), "draft")

    def create_draft_by_queue_id(self, queue_id, name, description):
        """create a draft by queue id"""
        d = {"name": name, "description": description}
        return post(self.session, self.url, d, str(queue_id), "draft")

    def delete_draft_by_queue_id(self, queue_id):
        """delete a draft by queue id"""
        d = None
        return delete(self.session, self.url, d, str(queue_id), "draft")

    def get_draft_by_queue_id(self, queue_id):
        """get a draft by queue id"""
        return get(self.session, self.url, str(queue_id), "draft")


class TagsClient(Endpoint):
    def get_all(self):
        return get(self.session, self.url)

    def create(self, name, group):
        d = {"name": name, "group": group}
        return post(self.session, self.url, d)

    def delete_by_id(self, tag_id):
        d = None
        return delete(self.session, self.url, d, str(tag_id))

    def get_by_id(self, tag_id):
        return get(self.session, self.url, str(tag_id))

    def modify_by_id(self, tag_id, name):
        d = {"name": name}
        return put(self.session, self.url, d, str(tag_id))

    def get_resources_by_id(self, tag_id):
        return get(self.session, self.url, str(tag_id), "resources")


class EntrypointsClient(Endpoint, HasTagsProvider):
    def __init__(self, session, ep_name, address, api_version):
        Endpoint.__init__(self, session, ep_name, address, api_version)
        HasTagsProvider.__init__(self, self.url, self.session)

    def get_all(self):
        return get(self.session, self.url)

    def create(self, group, name, description, taskGraph, parameters, queues, plugins):
        d = {
            "group": group,
            "name": name,
            "description": description,
            "taskGraph": taskGraph,
            "parameters": parameters,
            "queues": queues,
            "plugins": plugins,
        }
        return post(self.session, self.url, d)

    def create_draft(
        self, group, name, description, taskGraph, parameters, queues, plugins
    ):
        d = {
            "group": group,
            "name": name,
            "description": description,
            "taskGraph": taskGraph,
            "parameters": parameters,
            "queues": queues,
            "plugins": plugins,
        }
        return post(self.session, self.url, d, "drafts")

    def get_drafts(self):
        return get(self.session, self.url, "drafts")

    def modify_draft_by_draft_id(
        self, draft_id, name, description, taskGraph, parameters, queues
    ):
        d = {
            "name": name,
            "description": description,
            "taskGraph": taskGraph,
            "parameters": parameters,
            "queues": queues,
        }
        return put(self.session, self.url, d, "drafts", str(draft_id))

    def get_draft_by_draft_id(self, draft_id):
        return get(self.session, self.url, "drafts", str(draft_id))

    def delete_draft_by_draft_id(self, draft_id):
        d = None
        return delete(self.session, self.url, d, "drafts", str(draft_id))

    def modify_by_id(
        self, entrypoint_id, name, description, taskGraph, parameters, queues
    ):
        d = {
            "name": name,
            "description": description,
            "taskGraph": taskGraph,
            "parameters": parameters,
            "queues": queues,
        }
        return put(self.session, self.url, d, str(entrypoint_id))

    def get_by_id(self, entrypoint_id):
        return get(self.session, self.url, str(entrypoint_id))

    def delete_by_id(self, entrypoint_id):
        d = None
        return delete(self.session, self.url, d, str(entrypoint_id))

    def modify_draft_by_entrypoint_id(
        self, entrypoint_id, name, description, taskGraph, parameters, queues, plugins
    ):
        d = {
            "name": name,
            "description": description,
            "taskGraph": taskGraph,
            "parameters": parameters,
            "queues": queues,
            "plugins": plugins,
        }
        return put(self.session, self.url, d, str(entrypoint_id), "draft")

    def create_draft_by_entrypoint_id(
        self, entrypoint_id, name, description, taskGraph, parameters, queues, plugins
    ):
        d = {
            "name": name,
            "description": description,
            "taskGraph": taskGraph,
            "parameters": parameters,
            "queues": queues,
            "plugins": plugins,
        }
        return post(self.session, self.url, d, str(entrypoint_id), "draft")

    def get_draft_by_entrypoint_id(self, entrypoint_id):
        return get(self.session, self.url, str(entrypoint_id), "draft")

    def delete_draft_by_entrypoint_id(self, entrypoint_id):
        d = None
        return delete(self.session, self.url, d, str(entrypoint_id), "draft")

    def get_plugins_by_entrypoint_id(self, entrypoint_id):
        return get(self.session, self.url, str(entrypoint_id), "plugins")

    def add_plugins_by_entrypoint_id(self, entrypoint_id, plugins):
        d = {"plugins": plugins}
        return post(self.session, self.url, d, str(entrypoint_id), "plugins")

    def get_plugins_by_entrypoint_id_plugin_id(self, entrypoint_id, plugin_id):
        return get(
            self.session, self.url, str(entrypoint_id), "plugins", str(plugin_id)
        )

    def delete_plugins_by_entrypoint_id_plugin_id(self, entrypoint_id, plugin_id):
        d = None
        return delete(
            self.session, self.url, d, str(entrypoint_id), "plugins", str(plugin_id)
        )

    def modify_queues_by_entrypoint_id(self, entrypoint_id, ids):
        d = {"ids": ids}
        return put(self.session, self.url, d, str(entrypoint_id), "queues")

    def add_queues_by_entrypoint_id(self, entrypoint_id, ids):
        d = {"ids": ids}
        return post(self.session, self.url, d, str(entrypoint_id), "queues")

    def get_queues_by_entrypoint_id(self, entrypoint_id):
        return get(self.session, self.url, str(entrypoint_id), "queues")

    def delete_queues_by_entrypoint_id(self, entrypoint_id):
        d = None
        return delete(self.session, self.url, d, str(entrypoint_id), "queues")

    def delete_queues_by_entrypoint_id_queue_id(self, entrypoint_id, queue_id):
        d = None
        return delete(
            self.session, self.url, d, str(entrypoint_id), "queues", str(queue_id)
        )

    def get_snapshots_by_entrypoint_id(self, entrypoint_id):
        return get(self.session, self.url, str(entrypoint_id), "snapshots")

    def get_snapshots_by_entrypoint_id_snapshot_id(self, entrypoint_id, snapshot_id):
        return get(
            self.session, self.url, str(entrypoint_id), "snapshots", str(snapshot_id)
        )


class ExperimentsClient(Endpoint, HasTagsProvider):
    def __init__(self, session, ep_name, address, api_version):
        Endpoint.__init__(self, session, ep_name, address, api_version)
        HasTagsProvider.__init__(self, self.url, self.session)

    def get_all(self):
        return get(self.session, self.url)

    def create(self, group, name, description, entrypoints):
        d = {
            "group": group,
            "name": name,
            "description": description,
            "entrypoints": entrypoints,
        }
        return post(self.session, self.url, d)

    def get_drafts(self):
        return get(self.session, self.url, "drafts")

    def create_draft(self, group, name, description, entrypoints):
        d = {
            "group": group,
            "name": name,
            "description": description,
            "entrypoints": entrypoints,
        }
        return post(self.session, self.url, d, "drafts")

    def get_drafts_by_draft_id(self, draft_id):
        return get(self.session, self.url, "drafts", str(draft_id))

    def modify_drafts_by_draft_id(self, draft_id, name, description, entrypoints):
        d = {"name": name, "description": description, "entrypoints": entrypoints}
        return put(self.session, self.url, d, "drafts", str(draft_id))

    def delete_drafts_by_draft_id(self, draft_id):
        d = None
        return delete(self.session, self.url, d, "drafts", str(draft_id))

    def get_by_id(self, experiment_id):
        return get(self.session, self.url, str(experiment_id))

    def modify_by_id(self, experiment_id, name, description, entrypoints):
        d = {"name": name, "description": description, "entrypoints": entrypoints}
        return put(self.session, self.url, d, str(experiment_id))

    def delete_by_id(self, experiment_id):
        d = None
        return delete(self.session, self.url, d, str(experiment_id))

    def get_draft_by_experiment_id(self, experiment_id):
        return get(self.session, self.url, str(experiment_id), "draft")

    def modify_draft_by_experiment_id(
        self, experiment_id, name, description, entrypoints
    ):
        d = {"name": name, "description": description, "entrypoints": entrypoints}
        return put(self.session, self.url, d, str(experiment_id), "draft")

    def create_draft_by_experiment_id(
        self, experiment_id, name, description, entrypoints
    ):
        d = {"name": name, "description": description, "entrypoints": entrypoints}
        return post(self.session, self.url, d, str(experiment_id), "draft")

    def delete_draft_by_experiment_id(self, experiment_id):
        d = None
        return delete(self.session, self.url, d, str(experiment_id), "draft")

    def get_entrypoints_by_experiment_id(self, experiment_id):
        return get(self.session, self.url, str(experiment_id), "entrypoints")

    def modify_entrypoints_by_experiment_id(self, experiment_id, ids):
        d = {"ids": ids}
        return put(self.session, self.url, d, str(experiment_id), "entrypoints")

    def add_entrypoints_by_experiment_id(self, experiment_id, ids):
        d = {"ids": ids}
        return post(self.session, self.url, d, str(experiment_id), "entrypoints")

    def delete_entrypoints_by_experiment_id(self, experiment_id):
        d = None
        return delete(self.session, self.url, d, str(experiment_id), "entrypoints")

    def delete_entrypoints_by_experiment_id_entrypoint_id(
        self, experiment_id, entrypoint_id
    ):
        d = None
        return delete(
            self.session,
            self.url,
            d,
            str(experiment_id),
            "entrypoints",
            str(entrypoint_id),
        )

    def get_jobs_by_experiment_id(self, experiment_id):
        return get(self.session, self.url, str(experiment_id), "jobs")

    def create_jobs_by_experiment_id(
        self, experiment_id, description, queue, entrypoint, values, timeout
    ):
        d = {
            "description": description,
            "queue": queue,
            "entrypoint": entrypoint,
            "values": values,
            "timeout": timeout,
        }
        return post(self.session, self.url, d, str(experiment_id), "jobs")

    def get_jobs_by_experiment_id_job_id(self, experiment_id, job_id):
        return get(self.session, self.url, str(experiment_id), "jobs", str(job_id))

    def delete_jobs_by_experiment_id_job_id(self, experiment_id, job_id):
        d = None
        return delete(
            self.session, self.url, d, str(experiment_id), "jobs", str(job_id)
        )

    def get_jobs_status_by_experiment_id_job_id(self, experiment_id, job_id):
        return get(
            self.session, self.url, str(experiment_id), "jobs", str(job_id), "status"
        )

    def modify_jobs_status_by_experiment_id_job_id(self, experiment_id, job_id, status):
        d = {"status": status}
        return put(
            self.session, self.url, d, str(experiment_id), "jobs", str(job_id), "status"
        )

    def get_snapshots_by_experiment_id(self, experiment_id):
        return get(self.session, self.url, str(experiment_id), "snapshots")

    def get_snapshots_by_experiment_id_snapshot_id(self, experiment_id, snapshot_id):
        return get(
            self.session, self.url, str(experiment_id), "snapshots", str(snapshot_id)
        )


class JobsClient(Endpoint, HasTagsProvider):
    def __init__(self, session, ep_name, address, api_version):
        Endpoint.__init__(self, session, ep_name, address, api_version)
        HasTagsProvider.__init__(self, self.url, self.session)

    def get_all(self):
        return get(self.session, self.url)

    def delete_by_id(self, job_id):
        d = None
        return delete(self.session, self.url, d, str(job_id))

    def get_by_id(self, job_id):
        return get(self.session, self.url, str(job_id))

    def get_snapshots_by_job_id(self, job_id):
        return get(self.session, self.url, str(job_id), "snapshots")

    def get_snapshots_by_job_id_snapshot_id(self, job_id, snapshot_id):
        return get(self.session, self.url, str(job_id), "snapshots", str(snapshot_id))

    def get_status_by_job_id(self, job_id):
        return get(self.session, self.url, str(job_id), "status")


class PluginsClient(Endpoint, HasTagsProvider):
    def __init__(self, session, ep_name, address, api_version):
        Endpoint.__init__(self, session, ep_name, address, api_version)
        HasTagsProvider.__init__(self, self.url, self.session)

    def get_all(self):
        return get(self.session, self.url)

    def create(self, group, name, description):
        d = {"group": group, "name": name, "description": description}
        return post(self.session, self.url, d)

    def get_all_drafts(self):
        return get(self.session, self.url, "drafts")

    def create_draft(self, group, name, description):
        d = {"group": group, "name": name, "description": description}
        return post(self.session, self.url, d, "drafts")

    def get_draft_by_draft_id(self, plugin_id):
        return get(self.session, self.url, "drafts", str(plugin_id))

    def modify_draft_by_draft_id(self, plugin_id, name, description):
        d = {"name": name, "description": description}
        return put(self.session, self.url, d, "drafts", str(plugin_id))

    def delete_draft_by_draft_id(self, plugin_id):
        d = None
        return delete(self.session, self.url, d, "drafts", str(plugin_id))

    def get_by_id(self, plugin_id):
        return get(self.session, self.url, str(plugin_id))

    def modify_by_id(self, plugin_id, name, description):
        d = {"name": name, "description": description}
        return put(self.session, self.url, d, str(plugin_id))

    def delete_by_id(self, plugin_id):
        d = None
        return delete(self.session, self.url, d, str(plugin_id))

    def get_draft_by_plugin_id(self, plugin_id):
        return get(self.session, self.url, str(plugin_id), "draft")

    def modify_draft_by_plugin_id(self, plugin_id, name, description):
        d = {"name": name, "description": description}
        return put(self.session, self.url, d, str(plugin_id), "draft")

    def create_draft_by_plugin_id(self, plugin_id, name, description):
        d = {"name": name, "description": description}
        return post(self.session, self.url, d, str(plugin_id), "draft")

    def delete_draft_by_plugin_id(self, plugin_id):
        d = None
        return delete(self.session, self.url, d, str(plugin_id), "draft")

    def get_files_by_plugin_id(self, plugin_id):
        return get(self.session, self.url, str(plugin_id), "files")

    def create_files_by_plugin_id(
        self, plugin_id, filename, contents, description, *plugins
    ):
        d = {
            "filename": filename,
            "contents": contents,
            "description": description,
            "tasks": [plugin.as_dict() for plugin in plugins],
        }
        return post(self.session, self.url, d, str(plugin_id), "files")

    def delete_files_by_plugin_id(self, plugin_id):
        d = None
        return delete(self.session, self.url, d, str(plugin_id), "files")

    def get_files_drafts_by_plugin_id(self, plugin_id):
        return get(self.session, self.url, str(plugin_id), "files", "drafts")

    def create_files_drafts_by_plugin_id(
        self, plugin_id, filename, contents, description, *plugins
    ):
        d = {
            "filename": filename,
            "contents": contents,
            "description": description,
            "tasks": [plugin.as_dict() for plugin in plugins],
        }
        return post(self.session, self.url, d, str(plugin_id), "files", "drafts")

    def get_files_drafts_by_plugin_id_draft_id(self, plugin_id, drafts_id):
        return get(
            self.session, self.url, str(plugin_id), "files", "drafts", str(drafts_id)
        )

    def modify_files_drafts_by_plugin_id_draft_id(
        self, plugin_id, drafts_id, filename, contents, description, *plugins
    ):
        d = {
            "filename": filename,
            "contents": contents,
            "description": description,
            "tasks": [plugin.as_dict() for plugin in plugins],
        }
        return put(
            self.session, self.url, d, str(plugin_id), "files", "drafts", str(drafts_id)
        )

    def delete_files_drafts_by_plugin_id_draft_id(self, plugin_id, drafts_id):
        d = None
        return delete(
            self.session, self.url, d, str(plugin_id), "files", "drafts", str(drafts_id)
        )

    def get_files_by_plugin_id_file_id(self, plugin_id, file_id):
        return get(self.session, self.url, str(plugin_id), "files", str(file_id))

    def modify_files_by_plugin_id_file_id(
        self, plugin_id, file_id, filename, contents, description, *plugins
    ):
        d = {
            "filename": filename,
            "contents": contents,
            "description": description,
            "tasks": [plugin.as_dict() for plugin in plugins],
        }
        return put(self.session, self.url, d, str(plugin_id), "files", str(file_id))

    def delete_files_by_plugin_id_file_id(self, plugin_id, file_id):
        d = None
        return delete(self.session, self.url, d, str(plugin_id), "files", str(file_id))

    def get_files_draft_by_plugin_id_file_id(self, plugin_id, file_id):
        return get(
            self.session, self.url, str(plugin_id), "files", str(file_id), "draft"
        )

    def modify_files_draft_by_plugin_id_file_id(
        self, plugin_id, file_id, filename, contents, description, *plugins
    ):
        d = {
            "filename": filename,
            "contents": contents,
            "description": description,
            "tasks": [plugin.as_dict() for plugin in plugins],
        }
        return put(
            self.session, self.url, d, str(plugin_id), "files", str(file_id), "draft"
        )

    def delete_files_draft_by_plugin_id_file_id(self, plugin_id, file_id):
        d = None
        return delete(
            self.session, self.url, d, str(plugin_id), "files", str(file_id), "draft"
        )

    def create_files_draft_by_plugin_id_file_id(
        self, plugin_id, file_id, filename, contents, description, *plugins
    ):
        d = {
            "filename": filename,
            "contents": contents,
            "description": description,
            "tasks": [plugin.as_dict() for plugin in plugins],
        }
        return post(
            self.session, self.url, d, str(plugin_id), "files", str(file_id), "draft"
        )

    def get_snapshots_by_plugin_id_file_id(self, plugin_id, file_id):
        return get(
            self.session, self.url, str(plugin_id), "files", str(file_id), "snapshots"
        )

    def get_snapshots_by_plugin_id_file_id_snapshot_id(
        self, plugin_id, file_id, snapshot_id
    ):
        return get(
            self.session,
            self.url,
            str(plugin_id),
            "files",
            str(file_id),
            "snapshots",
            str(snapshot_id),
        )

    def get_tags_by_plugin_id_file_id(self, plugin_id, file_id):
        return get(
            self.session, self.url, str(plugin_id), "files", str(file_id), "tags"
        )

    def modify_tags_by_plugin_id_file_id(self, plugin_id, file_id, ids):
        d = {"ids": ids}
        return put(
            self.session, self.url, d, str(plugin_id), "files", str(file_id), "tags"
        )

    def delete_tags_by_plugin_id_file_id(self, plugin_id, file_id):
        d = None
        return delete(
            self.session, self.url, d, str(plugin_id), "files", str(file_id), "tags"
        )

    def add_tags_by_plugin_id_file_id(self, plugin_id, file_id, ids):
        d = {"ids": ids}
        return post(
            self.session, self.url, d, str(plugin_id), "files", str(file_id), "tags"
        )

    def delete_tags_by_plugin_id_file_id_tag_id(self, plugin_id, file_id, tag_id):
        d = None
        return delete(
            self.session,
            self.url,
            d,
            str(plugin_id),
            "files",
            str(file_id),
            "tags",
            str(tag_id),
        )

    def get_snapshots_by_plugin_id(self, plugin_id):
        return get(self.session, self.url, str(plugin_id), "snapshots")

    def get_snapshot_by_plugin_id_snapshot_id(self, plugin_id, snapshot_id):
        return get(
            self.session, self.url, str(plugin_id), "snapshots", str(snapshot_id)
        )


class PluginParameterTypesClient(Endpoint):
    def get_all(self):
        return get(self.session, self.url)

    def create(self, group, name, description, structure):
        d = {
            "group": group,
            "name": name,
            "description": description,
            "structure": structure,
        }
        return post(self.session, self.url, d)

    def get_by_id(self, type_id):
        return get(self.session, self.url, str(type_id))

    def modify_by_id(self, type_id, name, description, structure):
        d = {"name": name, "description": description, "structure": structure}
        return put(self.session, self.url, d, str(type_id))

    def delete_by_id(self, type_id):
        d = None
        return delete(self.session, self.url, d, str(type_id))


class PluginTask(object):
    def __init__(self, name, inputs, outputs, client):
        self.name = name
        self.inputs = inputs  # expects [(name1, type1), (name2, type2) ...]
        self.outputs = outputs  # expects [(name1, type1), (name2, type2) ...]
        self.client = client

    def convert_params_to_ids(self, mappings):
        """this converts parameters to registered ids using a
        mapping from register_unregistered_types"""
        return [(i[0], mappings[i[1]]) for i in self.inputs], [
            (o[0], mappings[o[1]]) for o in self.outputs
        ]

    def register_unregistered_types(self, group=1):
        """checks all the types in inputs/outputs and
        register things that aren't registered"""
        registered_types = (
            self.client.pluginParameterTypes.get_all()
        )  # get all registered types
        types_used_in_plugin = set(
            [m[1] for m in self.inputs] + [m[1] for m in self.outputs]
        )  # get all types for this plugin
        types_to_id = {}
        for registered in registered_types[
            "data"
        ]:  # add registered types to our dictionary
            types_to_id[str(registered["name"])] = str(registered["id"])
        for used in types_used_in_plugin:
            used = str(used)
            if used not in types_to_id:  # not yet registered, so register it
                response = self.client.pluginParameterTypes.create(
                    group, used, used + " plugin parameter", structure={}
                )
                types_to_id[used] = str(response["id"])
        return types_to_id  # mapping of types to ids

    def as_dict(self, mappings=None):
        """convert it to a dict to be sent to the RESTAPI"""
        if mappings is None:
            mappings = self.register_unregistered_types()
        ins, outs = self.convert_params_to_ids(mappings)
        return {
            "name": self.name,
            "inputParams": [
                {"name": param[0], "parameterType": param[1]} for param in ins
            ],
            "outputParams": [
                {"name": param[0], "parameterType": param[1]} for param in outs
            ],
        }
