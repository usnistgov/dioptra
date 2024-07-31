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
import structlog
from structlog.stdlib import BoundLogger

from .auth import AuthClient
from .base import DioptraSession
from .users import UsersClient

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class DioptraClient(object):
    def __init__(self, session: DioptraSession) -> None:
        self._session = session
        self._users = UsersClient(session)
        self._auth = AuthClient(session)
        # self._queues = QueuesClient(session)
        # self._groups = GroupsClient(session)
        # self._tags = TagsClient(session)
        # self._plugins = PluginsClient(session)
        # self._pluginParameterTypes = PluginParameterTypesClient(session)
        # self._experiments = ExperimentsClient(session)
        # self._jobs = JobsClient(session)
        # self._entrypoints = EntrypointsClient(session)
        # self._models = ModelsClient(session)
        # self._artifacts = ArtifactsClient(session)

    @property
    def users(self):
        return self._users

    @property
    def auth(self):
        return self._auth

    # @property
    # def queues(self):
    #     return self._queues

    # @property
    # def groups(self):
    #     return self._groups

    # @property
    # def tags(self):
    #     return self._tags

    # @property
    # def plugins(self):
    #     return self._plugins

    # @property
    # def pluginParameterTypes(self):
    #     return self._pluginParameterTypes

    # @property
    # def experiments(self):
    #     return self._experiments

    # @property
    # def jobs(self):
    #     return self._jobs

    # @property
    # def entrypoints(self):
    #     return self._entrypoints

    # @property
    # def models(self):
    #     return self._models

    # @property
    # def artifacts(self):
    #     return self._artifacts

    def close(self) -> None:
        self._session.close()


def connect_dioptra_client(address: str) -> DioptraClient:
    from .sessions import DioptraRequestsSession

    return DioptraClient(session=DioptraRequestsSession(address))
