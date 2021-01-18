import uuid
from typing import List, Optional

import structlog
from flask import jsonify, request
from flask.wrappers import Response
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from .errors import QueueDoesNotExistError, QueueRegistrationError
from .interface import QueueUpdateInterface
from .model import Queue, QueueRegistrationForm, QueueRegistrationFormData
from .schema import QueueNameUpdateSchema, QueueRegistrationSchema, QueueSchema
from .service import QueueService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "Queue",
    description="Endpoint for registering new job queues.",
)


@api.route("/")
class QueueResource(Resource):
    @inject
    def __init__(self, *args, queue_service: QueueService, **kwargs) -> None:
        self._queue_service = queue_service
        super().__init__(*args, **kwargs)

    @responds(schema=QueueSchema(many=True), api=api)
    def get(self) -> List[Queue]:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="queue", request_type="GET"
        )  # noqa: F841
        log.info("Request received")
        return self._queue_service.get_all_unlocked(log=log)

    @accepts(QueueRegistrationSchema, api=api)
    @responds(schema=QueueSchema, api=api)
    def post(self) -> Queue:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="queue", request_type="POST"
        )  # noqa: F841
        queue_registration_form: QueueRegistrationForm = QueueRegistrationForm()

        log.info("Request received")

        if not queue_registration_form.validate_on_submit():
            log.error("Form validation failed")
            raise QueueRegistrationError

        log.info("Form validation successful")
        queue_registration_form_data: QueueRegistrationFormData = (
            self._queue_service.extract_data_from_form(
                queue_registration_form=queue_registration_form, log=log
            )
        )
        return self._queue_service.create(
            queue_registration_form_data=queue_registration_form_data, log=log
        )


@api.route("/<int:queueId>")
@api.param("queueId", "Unique queue identifier")
class QueueIdResource(Resource):
    @inject
    def __init__(self, *args, queue_service: QueueService, **kwargs) -> None:
        self._queue_service = queue_service
        super().__init__(*args, **kwargs)

    @responds(schema=QueueSchema, api=api)
    def get(self, queueId: int) -> Queue:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="queueId", request_type="GET"
        )  # noqa: F841
        log.info("Request received", queue_id=queueId)
        queue: Optional[Queue] = self._queue_service.get_by_id(queueId, log=log)

        if queue is None:
            log.error("Queue not found", queue_id=queueId)
            raise QueueDoesNotExistError

        return queue

    def delete(self, queueId: int) -> Response:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="queueId", request_type="DELETE"
        )  # noqa: F841
        log.info("Request received", queue_id=queueId)
        id: List[int] = self._queue_service.delete_queue(queueId, log=log)

        return jsonify(dict(status="Success", id=id))  # type: ignore

    @accepts(schema=QueueNameUpdateSchema, api=api)
    @responds(schema=QueueSchema, api=api)
    def put(self, queueId: int) -> Queue:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="queueId", request_type="PUT"
        )  # noqa: F841
        changes: QueueUpdateInterface = request.parsed_obj  # type: ignore
        queue: Optional[Queue] = self._queue_service.get_by_id(queueId, log=log)

        if queue is None:
            log.error("Queue not found", queue_id=queueId)
            raise QueueDoesNotExistError

        queue = self._queue_service.rename_queue(
            queue=queue, new_name=changes["name"], log=log
        )

        return queue


@api.route("/<int:queueId>/lock")
@api.param("queueId", "Unique queue identifier")
class QueueIdLockResource(Resource):
    @inject
    def __init__(self, *args, queue_service: QueueService, **kwargs) -> None:
        self._queue_service = queue_service
        super().__init__(*args, **kwargs)

    def delete(self, queueId: int) -> Response:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="QueueIdLock", request_type="DELETE"
        )  # noqa: F841
        log.info("Request received", queue_id=queueId)
        queue: Optional[Queue] = self._queue_service.get_by_id(queueId, log=log)

        if queue is None:
            log.error("Queue not found", queue_id=queueId)
            raise QueueDoesNotExistError

        id: List[int] = self._queue_service.unlock_queue(queue, log=log)

        return jsonify(dict(status="Success", id=id))  # type: ignore

    def put(self, queueId: int) -> Queue:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="QueueIdLock", request_type="PUT"
        )  # noqa: F841
        log.info("Request received", queue_id=queueId)
        queue: Optional[Queue] = self._queue_service.get_by_id(queueId, log=log)

        if queue is None:
            log.error("Queue not found", queue_id=queueId)
            raise QueueDoesNotExistError

        id: List[int] = self._queue_service.lock_queue(queue, log=log)

        return jsonify(dict(status="Success", id=id))  # type: ignore


@api.route("/name/<string:queueName>")
@api.param("queueName", "Unique queue name")
class QueueNameResource(Resource):
    @inject
    def __init__(self, *args, queue_service: QueueService, **kwargs) -> None:
        self._queue_service = queue_service
        super().__init__(*args, **kwargs)

    @responds(schema=QueueSchema, api=api)
    def get(self, queueName: str) -> Queue:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="queueName", request_type="GET"
        )  # noqa: F841
        log.info("Request received", queue_name=queueName)
        queue: Optional[Queue] = self._queue_service.get_by_name(
            queue_name=queueName, log=log
        )

        if queue is None:
            log.error("Queue not found", queue_name=queueName)
            raise QueueDoesNotExistError

        return queue

    def delete(self, queueName: str) -> Response:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="queueName",
            queue_name=queueName,
            request_type="DELETE",
        )  # noqa: F841
        log.info("Request received")
        queue: Optional[Queue] = self._queue_service.get_by_name(
            queue_name=queueName, log=log
        )

        if queue is None:
            return jsonify(dict(status="Success", id=[]))  # type: ignore

        id: List[int] = self._queue_service.delete_queue(queue_id=queue.queue_id)

        return jsonify(dict(status="Success", id=id))  # type: ignore

    @accepts(schema=QueueNameUpdateSchema, api=api)
    @responds(schema=QueueSchema, api=api)
    def put(self, queueName: str) -> Queue:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="queueName", request_type="PUT"
        )  # noqa: F841
        changes: QueueUpdateInterface = request.parsed_obj  # type: ignore
        queue: Optional[Queue] = self._queue_service.get_by_name(
            queue_name=queueName, log=log
        )

        if queue is None:
            log.error("Queue not found", queue_name=queueName)
            raise QueueDoesNotExistError

        queue = self._queue_service.rename_queue(
            queue=queue, new_name=changes["name"], log=log
        )

        return queue


@api.route("/name/<string:queueName>/lock")
@api.param("queueName", "Unique queue name")
class QueueNameLockResource(Resource):
    @inject
    def __init__(self, *args, queue_service: QueueService, **kwargs) -> None:
        self._queue_service = queue_service
        super().__init__(*args, **kwargs)

    def delete(self, queueName: str) -> Response:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="QueueNameLock",
            request_type="DELETE",
        )  # noqa: F841
        log.info("Request received", queue_name=queueName)
        queue: Optional[Queue] = self._queue_service.get_by_name(queueName, log=log)

        if queue is None:
            log.error("Queue not found", queue_name=queueName)
            raise QueueDoesNotExistError

        id: List[int] = self._queue_service.unlock_queue(queue, log=log)
        name: List[str] = [queueName] if id else []

        return jsonify(dict(status="Success", name=name))  # type: ignore

    def put(self, queueName: str) -> Queue:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="QueueNameLock", request_type="PUT"
        )  # noqa: F841
        log.info("Request received", queue_name=queueName)
        queue: Optional[Queue] = self._queue_service.get_by_name(queueName, log=log)

        if queue is None:
            log.error("Queue not found", queue_name=queueName)
            raise QueueDoesNotExistError

        id: List[int] = self._queue_service.lock_queue(queue, log=log)
        name: List[str] = [queueName] if id else []

        return jsonify(dict(status="Success", name=name))  # type: ignore
