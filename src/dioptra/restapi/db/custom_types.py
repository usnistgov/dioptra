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
"""Custom SQLAlchemy data types for the REST API database."""
import datetime
import uuid

from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(32), storing as stringified hex
    values.

    Note:
        This implementation is adapted from the following section of the SQLAlchemy
        documentation:
        https://docs.sqlalchemy.org/en/20/core/custom_types.html#backend-agnostic-guid-type
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())

        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        elif dialect.name == "postgresql":
            return str(value)

        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value).hex

            else:
                # hexstring
                return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)

            return value


class TZDateTime(TypeDecorator):
    """Timezone-aware timestamps stored as timezone-naive UTC timestamps.

    Converts incoming timestamps with timezone information to UTC and then strips out
    the timezone information before storing in the database. This implementation is
    preferred because it is compatible with all database backends.

    Note:
        This implementation is adapted from the following section of the SQLAlchemy
        documentation:
        https://docs.sqlalchemy.org/en/20/core/custom_types.html#store-timezone-aware-timestamps-as-timezone-naive-utc
    """

    impl = SADateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        if not value.tzinfo or value.tzinfo.utcoffset(value) is None:
            raise TypeError("tzinfo is required")

        value = value.astimezone(datetime.timezone.utc).replace(tzinfo=None)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = value.replace(tzinfo=datetime.timezone.utc)

        return value
