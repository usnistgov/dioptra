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
"""The SQLAlchemy Metadata and Flask integration for the Dioptra database.

For further information about the SQLAlchemy MetaData class, see:
https://docs.sqlalchemy.org/en/20/core/metadata.html

For further information about configuring the SQLAlchemy constraint naming conventions,
see:
https://docs.sqlalchemy.org/en/20/core/constraints.html#constraint-naming-conventions
"""
import datetime
import uuid
from sqlite3 import Connection as SQLite3Connection
from typing import Annotated, Any, Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON, BigInteger, Boolean, Integer, MetaData, String, Text, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, mapped_column

from .custom_types import GUID, TZDateTime

intpk = Annotated[
    int, mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
]
bigint = Annotated[int, mapped_column(BigInteger().with_variant(Integer, "sqlite"))]
bigintnovariant = Annotated[int, mapped_column(BigInteger())]
guid = Annotated[uuid.UUID, mapped_column(GUID())]
datetimetz = Annotated[datetime.datetime, mapped_column(TZDateTime())]
optionalbigint = Annotated[
    Optional[int],
    mapped_column(BigInteger().with_variant(Integer, "sqlite"), nullable=True),
]
optionaldatetimetz = Annotated[Optional[datetime.datetime], mapped_column(TZDateTime())]
optionaljson_ = Annotated[Optional[dict[str, Any]], mapped_column(JSON)]
optionalstr = Annotated[Optional[str], mapped_column(Text(), nullable=True)]
optionalstr36 = Annotated[Optional[str], mapped_column(String(36), nullable=True)]
json_ = Annotated[dict[str, Any], mapped_column(MutableDict.as_mutable(JSON))]
str36 = Annotated[str, mapped_column(String(36))]
str255 = Annotated[str, mapped_column(String(255))]
text_ = Annotated[str, mapped_column(Text())]
bool_ = Annotated[bool, mapped_column(Boolean())]

_naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_obj = MetaData(naming_convention=_naming_convention)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(
    dbapi_connection: SQLite3Connection, connection_record: Any
) -> None:
    """Set 'PRAGMA foreign_keys=ON' for each new SQLite connection."""
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


class Base(DeclarativeBase, MappedAsDataclass):
    """The base ORM class."""

    metadata = metadata_obj


db = SQLAlchemy(model_class=Base)
