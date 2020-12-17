import datetime
from typing import List, Optional

import structlog
from injector import inject
from structlog import BoundLogger
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.app import db

from .errors import QueueAlreadyExistsError
from .model import Queue, QueueLock, QueueRegistrationForm, QueueRegistrationFormData
from .schema import QueueRegistrationFormSchema

LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


class QueueService(object):
    @inject
    def __init__(
        self,
        queue_registration_form_schema: QueueRegistrationFormSchema,
    ) -> None:
        self._queue_registration_form_schema = queue_registration_form_schema

    def create(
        self,
        queue_registration_form_data: QueueRegistrationFormData,
        **kwargs,
    ) -> Queue:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        queue_name: str = queue_registration_form_data["name"]

        if self.get_by_name(queue_name, log=log) is not None:
            raise QueueAlreadyExistsError

        timestamp = datetime.datetime.now()
        new_queue: Queue = Queue(
            queue_id=Queue.next_id(),
            name=queue_name,
            created_on=timestamp,
            last_modified=timestamp,
        )
        db.session.add(new_queue)
        db.session.commit()

        log.info(
            "Queue registration successful",
            queue_id=new_queue.queue_id,
            name=new_queue.name,
        )

        return new_queue

    @staticmethod
    def lock_queue(queue: Queue, **kwargs) -> List[int]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if queue.lock:
            return []

        queue.lock.append(QueueLock())
        db.session.commit()

        log.info("Queue locked", queue_id=queue.queue_id)

        return [queue.queue_id]

    @staticmethod
    def unlock_queue(queue: Queue, **kwargs) -> List[int]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if not queue.lock:
            return []

        db.session.delete(queue.lock[0])
        db.session.commit()

        log.info("Queue unlocked", queue_id=queue.queue_id)

        return [queue.queue_id]

    def delete_queue(self, queue_id: int, **kwargs) -> List[int]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        queue: Optional[Queue] = self.get_by_id(queue_id=queue_id)

        if queue is None:
            return []

        queue.update(changes={"is_deleted": True})
        db.session.commit()

        log.info("Queue deleted", queue_id=queue_id)

        return [queue_id]

    def rename_queue(self, queue: Queue, new_name: str, **kwargs) -> Queue:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        queue.update(changes={"name": new_name})
        db.session.commit()

        log.info("Queue renamed", queue_id=queue.queue_id, new_name=new_name)

        return queue

    @staticmethod
    def get_all(**kwargs) -> List[Queue]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Get full list of queues")

        return Queue.query.filter_by(is_deleted=False).all()  # type: ignore

    @staticmethod
    def get_all_unlocked(**kwargs) -> List[Queue]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Get full list of unlocked queues")

        return (  # type: ignore
            Queue.query.outerjoin(QueueLock, Queue.queue_id == QueueLock.queue_id)
            .filter(QueueLock.queue_id == None, Queue.is_deleted == False)  # noqa: E711
            .all()
        )

    @staticmethod
    def get_all_locked(**kwargs) -> List[Queue]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Get full list of locked queues")

        return (  # type: ignore
            Queue.query.join(QueueLock)
            .filter(Queue.is_deleted == False)  # noqa: E712
            .all()
        )

    @staticmethod
    def get_by_id(queue_id: int, **kwargs) -> Optional[Queue]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Get queue by id", queue_id=queue_id)

        return Queue.query.filter_by(  # type: ignore
            queue_id=queue_id, is_deleted=False
        ).first()

    @staticmethod
    def get_by_name(queue_name: str, **kwargs) -> Optional[Queue]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Get queue by name", queue_name=queue_name)

        return Queue.query.filter_by(  # type: ignore
            name=queue_name, is_deleted=False
        ).first()

    @staticmethod
    def get_unlocked_by_id(queue_id: int, **kwargs) -> Optional[Queue]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Get unlocked queue by id", queue_id=queue_id)

        return (  # type: ignore
            Queue.query.outerjoin(QueueLock, Queue.queue_id == QueueLock.queue_id)
            .filter(
                Queue.queue_id == queue_id,
                QueueLock.queue_id == None,  # noqa: E711
                Queue.is_deleted == False,
            )
            .first()
        )

    @staticmethod
    def get_unlocked_by_name(queue_name: str, **kwargs) -> Optional[Queue]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Get unlocked queue by name", queue_name=queue_name)

        return (  # type: ignore
            Queue.query.outerjoin(QueueLock, Queue.queue_id == QueueLock.queue_id)
            .filter(
                Queue.name == queue_name,
                QueueLock.queue_id == None,  # noqa: E711
                Queue.is_deleted == False,
            )
            .first()
        )

    def extract_data_from_form(
        self, queue_registration_form: QueueRegistrationForm, **kwargs
    ) -> QueueRegistrationFormData:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Extract data from queue registration form")
        data: QueueRegistrationFormData = self._queue_registration_form_schema.dump(
            queue_registration_form
        )

        return data
