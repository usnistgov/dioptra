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
        self._users = UsersClient(session, "users", address)
        self._auth = AuthClient(session, "auth", address)
        self._queues = QueuesClient(session, "queues", address)
        self._groups = GroupsClient(session, "groups", address)
        self._tags = TagsClient(session, "tags", address)
        self._plugins = PluginsClient(session, "plugins", address)
        self._pluginParameterTypes = PluginParameterTypesClient(
            session, "pluginParameterTypes", address
        )
        self._experiments = ExperimentsClient(session, "experiments", address)
        self._jobs = JobsClient(session, "jobs", address)
        self._entrypoints = EntrypointsClient(session, "entrypoints", address)
        self._models = ModelsClient(session, "models", address)
        self._artifacts = ArtifactsClient(session, "artifacts", address)
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

    @property
    def models(self):
        return self.get_endpoint(self._models)

    @property
    def artifacts(self):
        return self.get_endpoint(self._artifacts)

    def get_endpoint(self, ep):
        ep.session = self._session
        return ep


class HasTagsProvider(object):
    def __init__(self, url, session):
        self._tags = TagsProvider(url, session)

    @property
    def tags(self):
        return self.get_endpoint(self._tags)

    def get_endpoint(self, ep):
        ep.session = self._session
        return ep


class HasDraftsEndpoint(object):
    def __init__(self, url, session, address, fields, put_fields=None):
        self.draft_fields = fields
        self.put_fields = put_fields if put_fields is not None else fields
        self._drafts = DraftsEndpoint(url, self, session, "draft", address)

    @property
    def drafts(self):
        return self.get_endpoint(self._drafts)

    def get_endpoint(self, ep):
        ep.session = self._session
        return ep


class HasSubEndpointProvider(object):
    def __init__(self, url):
        self._url = url

    def idurl(self, ep_id):
        return urljoin(self._url, ep_id)


class Endpoint(object):
    def __init__(self, session, ep_name, address):
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

    @property
    def ep_name(self):
        return self._ep_name

    def def_endpoint(self, name):
        """creates base url for an endpoint by name"""
        return urlunparse(
            (self._scheme, self._netloc, urljoin(self._path, name + "/"), "", "", "")
        )

    def get_all(self, search=None, groupId=None, index=None, pageLength=None):
        """gets all resources"""
        return get(self.session, self.url, build_get_params(search=search, groupId=groupId, index=index, pageLength=pageLength))


class SubEndpoint(Endpoint):
    def __init__(self, parent, session, ep_name, address):
        Endpoint.__init__(self, session, ep_name, address)
        self._parent = parent  # parent should extend HasSubEndpointProvider

    def suburl(self, ep_id):
        return urljoin(self._parent.idurl(str(ep_id)), self.ep_name)

def build_get_params(**kwargs):
    kwargs = dict(filter(lambda item: item[1] != None, kwargs.items()))
    if (kwargs != {}):
        return '?' + '&'.join([str(a[0]) + '=' + str(a[1]) for a in kwargs.items()])
    else:
        return ''

class UsersClient(Endpoint):
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
    def get_by_id(self, gid):
        """get a group by id"""
        return get(self.session, self.url, str(gid))


class QueuesClient(Endpoint, HasDraftsEndpoint, HasSubEndpointProvider):
    def __init__(self, session, ep_name, address):
        Endpoint.__init__(self, session, ep_name, address)
        HasDraftsEndpoint.__init__(
            self, self.url, self.session, address, ["name", "description"]
        )
        HasSubEndpointProvider.__init__(self, self.url)

    def create(self, group, name, description):
        """create a queue"""
        d = {"group": group, "name": name, "description": description}
        return post(self.session, self.url, d)

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


class TagsClient(Endpoint):

    def create(self, group, name):
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


class EntrypointsClient(
    Endpoint, HasTagsProvider, HasDraftsEndpoint, HasSubEndpointProvider
):
    def __init__(self, session, ep_name, address):
        Endpoint.__init__(self, session, ep_name, address)
        HasTagsProvider.__init__(self, self.url, self.session)
        HasDraftsEndpoint.__init__(
            self,
            self.url,
            self.session,
            address,
            ["name", "description", "taskGraph", "parameters", "queues", "plugins"],
        )
        HasSubEndpointProvider.__init__(self, self.url)

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


class ExperimentsClient(
    Endpoint, HasTagsProvider, HasDraftsEndpoint, HasSubEndpointProvider
):
    def __init__(self, session, ep_name, address):
        Endpoint.__init__(self, session, ep_name, address)
        HasTagsProvider.__init__(self, self.url, self.session)
        HasDraftsEndpoint.__init__(
            self,
            self.url,
            self.session,
            address,
            ["name", "description", "entrypoints"],
        )
        HasSubEndpointProvider.__init__(self, self.url)

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

    def get_by_id(self, experiment_id):
        return get(self.session, self.url, str(experiment_id))

    def modify_by_id(self, experiment_id, name, description, entrypoints):
        d = {"name": name, "description": description, "entrypoints": entrypoints}
        return put(self.session, self.url, d, str(experiment_id))

    def delete_by_id(self, experiment_id):
        d = None
        return delete(self.session, self.url, d, str(experiment_id))

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
    def __init__(self, session, ep_name, address):
        Endpoint.__init__(self, session, ep_name, address)
        HasTagsProvider.__init__(self, self.url, self.session)

    def delete_by_id(self, job_id):
        d = None
        return delete(self.session, self.url, d, str(job_id))

    def get_by_id(self, job_id):
        return get(self.session, self.url, str(job_id))

    def get_mlflow_run_id(self, job_id):
        return get(self.session, self.url, str(job_id), "mlflowRun")

    def get_snapshots_by_job_id(self, job_id):
        return get(self.session, self.url, str(job_id), "snapshots")

    def get_snapshots_by_job_id_snapshot_id(self, job_id, snapshot_id):
        return get(self.session, self.url, str(job_id), "snapshots", str(snapshot_id))

    def get_status_by_job_id(self, job_id):
        return get(self.session, self.url, str(job_id), "status")


class PluginsClient(
    Endpoint, HasDraftsEndpoint, HasSubEndpointProvider, HasTagsProvider
):
    def __init__(self, session, ep_name, address):
        Endpoint.__init__(self, session, ep_name, address)
        HasTagsProvider.__init__(self, self.url, self.session)
        HasDraftsEndpoint.__init__(
            self, self.url, self.session, address, ["name", "description"]
        )
        HasSubEndpointProvider.__init__(self, self.url)
        self._files = PluginFilesClient(self, session, "files", address)

    @property
    def files(self):
        self._files.session = self.session
        return self._files

    def create(self, group, name, description):
        d = {"group": group, "name": name, "description": description}
        return post(self.session, self.url, d)

    def get_by_id(self, plugin_id):
        return get(self.session, self.url, str(plugin_id))

    def modify_by_id(self, plugin_id, name, description):
        d = {"name": name, "description": description}
        return put(self.session, self.url, d, str(plugin_id))

    def delete_by_id(self, plugin_id):
        d = None
        return delete(self.session, self.url, d, str(plugin_id))

    def get_snapshots_by_plugin_id(self, plugin_id):
        return get(self.session, self.url, str(plugin_id), "snapshots")

    def get_snapshot_by_plugin_id_snapshot_id(self, plugin_id, snapshot_id):
        return get(
            self.session, self.url, str(plugin_id), "snapshots", str(snapshot_id)
        )


class PluginFilesClient(SubEndpoint):
    def __init__(self, parent, session, ep_name, address):
        SubEndpoint.__init__(self, parent, session, ep_name, address)
        # HasTagsProvider.__init__(self, self.url, self.session)
        # HasDraftsEndpoint.__init__(self, self.url, self.session, address,
        #                              ["filename", "description"]
        #                          )
        # HasSubEndpointProvider.__init__(self, self.url)

    def get_files_by_plugin_id(self, plugin_id, search=None, groupId=None, index=None, pageLength=None):
        return get(self.session, self.suburl(plugin_id) + build_get_params(search=search, groupId=groupId, index=index, pageLength=pageLength))

    def create_files_by_plugin_id(
        self, plugin_id, filename, contents, description, plugins
    ):
        d = {
            "filename": filename,
            "contents": contents,
            "description": description,
            "tasks": plugins,
        }
        return post(self.session, self.suburl(plugin_id), d)

    def delete_files_by_plugin_id(self, plugin_id):
        d = None
        return delete(self.session, self.suburl(plugin_id), d)

    def get_files_drafts_by_plugin_id(self, plugin_id):
        return get(self.session, self.suburl(plugin_id), "drafts")

    def create_files_drafts_by_plugin_id(
        self, plugin_id, filename, contents, description, plugins
    ):
        d = {
            "filename": filename,
            "contents": contents,
            "description": description,
            "tasks": plugins,
        }
        return post(self.session, self.suburl(plugin_id), d, "drafts")

    def get_files_drafts_by_plugin_id_draft_id(self, plugin_id, drafts_id):
        return get(self.session, self.suburl(plugin_id), "drafts", str(drafts_id))

    def modify_files_drafts_by_plugin_id_draft_id(
        self, plugin_id, drafts_id, filename, contents, description, plugins
    ):
        d = {
            "filename": filename,
            "contents": contents,
            "description": description,
            "tasks": plugins,
        }
        return put(self.session, self.suburl(plugin_id), d, "drafts", str(drafts_id))

    def delete_files_drafts_by_plugin_id_draft_id(self, plugin_id, drafts_id):
        d = None
        return delete(self.session, self.suburl(plugin_id), d, "drafts", str(drafts_id))

    def get_files_by_plugin_id_file_id(self, plugin_id, file_id):
        return get(self.session, self.suburl(plugin_id), str(file_id))

    def modify_files_by_plugin_id_file_id(
        self, plugin_id, file_id, filename, contents, description, plugins
    ):
        d = {
            "filename": filename,
            "contents": contents,
            "description": description,
            "tasks": plugins,
        }
        return put(self.session, self.suburl(plugin_id), d, str(file_id))

    def delete_files_by_plugin_id_file_id(self, plugin_id, file_id):
        d = None
        return delete(self.session, self.suburl(plugin_id), d, str(file_id))

    def get_files_draft_by_plugin_id_file_id(self, plugin_id, file_id):
        return get(self.session, self.suburl(plugin_id), str(file_id), "draft")

    def modify_files_draft_by_plugin_id_file_id(
        self, plugin_id, file_id, filename, contents, description, plugins
    ):
        d = {
            "filename": filename,
            "contents": contents,
            "description": description,
            "tasks": plugins,
        }
        return put(self.session, self.suburl(plugin_id), d, str(file_id), "draft")

    def delete_files_draft_by_plugin_id_file_id(self, plugin_id, file_id):
        d = None
        return delete(self.session, self.suburl(plugin_id), d, str(file_id), "draft")

    def create_files_draft_by_plugin_id_file_id(
        self, plugin_id, file_id, filename, contents, description, plugins
    ):
        d = {
            "filename": filename,
            "contents": contents,
            "description": description,
            "tasks": plugins,
        }
        return post(self.session, self.suburl(plugin_id), d, str(file_id), "draft")

    def get_snapshots_by_plugin_id_file_id(self, plugin_id, file_id):
        return get(self.session, self.suburl(plugin_id), str(file_id), "snapshots")

    def get_snapshots_by_plugin_id_file_id_snapshot_id(
        self, plugin_id, file_id, snapshot_id
    ):
        return get(
            self.session,
            self.suburl(plugin_id),
            str(file_id),
            "snapshots",
            str(snapshot_id),
        )

    def get_tags_by_plugin_id_file_id(self, plugin_id, file_id):
        return get(self.session, self.suburl(plugin_id), str(file_id), "tags")

    def modify_tags_by_plugin_id_file_id(self, plugin_id, file_id, ids):
        d = {"ids": ids}
        return put(self.session, self.suburl(plugin_id), d, str(file_id), "tags")

    def delete_tags_by_plugin_id_file_id(self, plugin_id, file_id):
        d = None
        return delete(self.session, self.suburl(plugin_id), d, str(file_id), "tags")

    def add_tags_by_plugin_id_file_id(self, plugin_id, file_id, ids):
        d = {"ids": ids}
        return post(self.session, self.suburl(plugin_id), d, str(file_id), "tags")

    def delete_tags_by_plugin_id_file_id_tag_id(self, plugin_id, file_id, tag_id):
        d = None
        return delete(
            self.session, self.suburl(plugin_id), d, str(file_id), "tags", str(tag_id)
        )


class PluginParameterTypesClient(Endpoint):

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
        """this converts parameters to registered ids using a mapping
        from register_unregistered_types"""
        return [(i[0], mappings[i[1]]) for i in self.inputs], [
            (o[0], mappings[o[1]]) for o in self.outputs
        ]

    def register_unregistered_types(self, group=1):
        """checks all the types in inputs/outputs and register things that
        aren't registered"""
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


class ArtifactsClient(Endpoint):

    def create(self, group, description, job, uri):
        d = {"group": group, "description": description, "job": job, "uri": uri}
        return post(self.session, self.url, d)

    def get_by_id(self, artifact_id):
        return get(self.session, self.url, str(artifact_id))

    def modify_by_id(self, artifact_id, description):
        d = {"description": description}
        return put(self.session, self.url, d, str(artifact_id))

    def get_snapshots(self, artifact_id):
        return get(self.session, self.url, str(artifact_id), "snapshots")

    def get_snapshots_by_artifact_id_snapshot_id(self, artifact_id, snapshot_id):
        return get(
            self.session, self.url, str(artifact_id), "snapshots", str(snapshot_id)
        )


class ModelsClient(
    Endpoint, HasTagsProvider, HasDraftsEndpoint, HasSubEndpointProvider
):
    def __init__(self, session, ep_name, address):
        Endpoint.__init__(self, session, ep_name, address)
        HasSubEndpointProvider.__init__(self, self.url)
        HasTagsProvider.__init__(self, self.url, self.session)
        HasDraftsEndpoint.__init__(
            self, self.url, self.session, address, ["name", "description"]
        )

    def create(self, group, name, description):
        d = {"group": group, "name": name, "description": description}
        return post(self.session, self.url, d)

    def get_by_id(self, model_id):
        return get(self.session, self.url, str(model_id))

    def modify_by_id(self, model_id, name, description):
        d = {"name": name, "description": description}
        return put(self.session, self.url, d, str(model_id))

    def delete_by_id(self, model_id):
        d = None
        return delete(self.session, self.url, d, str(model_id))

    def get_snapshots_by_model_id(self, model_id):
        return get(self.session, self.url, str(model_id), "snapshots")

    def get_snapshot_by_plugin_id_model_id(self, model_id, snapshot_id):
        return get(self.session, self.url, str(model_id), "snapshots", str(snapshot_id))

    def get_versions_by_model_id(self, model_id):
        return get(self.session, self.url, str(model_id), "versions")

    def create_version_by_model_id(self, model_id, description, artifact):
        d = {"description": description, "artifact": artifact}
        return post(self.session, self.url, d, str(model_id), "versions")

    def modify_version_by_model_id_version_id(self, model_id, version_id, description):
        d = {"description": description}
        return put(
            self.session, self.url, d, str(model_id), "versions", str(version_id)
        )

    def get_version_by_model_id_version_id(self, model_id, version_id):
        return get(self.session, self.url, str(model_id), "versions", str(version_id))


class DraftsEndpoint(SubEndpoint):
    def __init__(self, base_url, parent, session, ep_name, address):
        SubEndpoint.__init__(self, parent, session, ep_name, address)
        self.base_url = base_url
        self.fields = parent.draft_fields  # array of field names
        self.put_fields = parent.put_fields  # used when PUT method differs from create

    @property
    def drafts_url(self):
        return urljoin(self.base_url, "drafts")

    # /something/id/draft

    def create_draft_for_resource(
        self, parent_id, *fields
    ):  # TODO: what to do about these parameters? they can be different
        d = {}
        for f in zip(self.fields, fields):
            d[f[0]] = f[1]
        return post(self.session, self.suburl(parent_id), d)

    def get_draft_for_resource(self, parent_id):
        return get(self.session, self.suburl(parent_id))

    def modify_draft_for_resource(self, parent_id, *fields):
        d = {}
        for f in zip(self.put_fields, fields):
            d[f[0]] = f[1]
        return put(self.session, self.suburl(parent_id), d)

    def delete_draft_for_resource(self, parent_id):
        d = None
        return delete(self.session, self.suburl(parent_id), d)

    # /something/drafts/

    def get_all(self, draftType=None, groupId=None, index=None, pageLength=None):
        """gets all drafts"""
        return get(self.session, self.url, build_get_params(draftType=draftType, groupId=groupId, index=index, pageLength=pageLength))

    def create(self, group_id, *fields):
        d = {"group": group_id}
        for f in zip(self.fields, fields):
            d[f[0]] = f[1]
        return post(self.session, self.drafts_url, d)

    def modify_by_draft_id(self, draft_id, *fields):
        d = {}
        for f in zip(self.put_fields, fields):
            d[f[0]] = f[1]
        return put(self.session, self.drafts_url, d, str(draft_id))

    def delete_by_draft_id(self, draft_id):
        d = None
        return delete(self.session, self.drafts_url, d, str(draft_id))

    def get_by_draft_id(self, draft_id):
        return get(self.session, self.drafts_url, str(draft_id))


class TagsProvider(object):
    def __init__(self, base_url, session):
        # SubEndpoint.__init__(self, session)
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