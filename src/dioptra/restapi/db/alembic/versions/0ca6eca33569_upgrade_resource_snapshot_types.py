"""Up/Down-grade resource snapshot types as delete/insert 'resource_snapshot' [GH-Issue #474]

Revision ID: 0ca6eca33569
Revises: 6a75ede23821
Create Date: 2024-12-12 00:47:23.575103

"""

from pprint import pprint
from typing import Annotated, Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy import delete, insert, select
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    sessionmaker,
)

### To test upgrade run:
"""
dioptra-db upgrade --revision 0ca6eca33569
"""
### Or if on version 6a75ede23821 and the only newer version is 0ca6eca33569
"""
dioptra-db upgrade
"""
### To downgrade run:
"""
dioptra-db downgrade 6a75ede23821
"""

# revision identifiers, used by Alembic.
revision = "0ca6eca33569"
down_revision = "6a75ede23821"
branch_labels = None
depends_on = None

text_ = Annotated[str, mapped_column(sa.Text())]


### DeclarativeBase does not allow direct subclassing !!!
class AlmaTable(DeclarativeBase, MappedAsDataclass):
    """The Mix-In Class of two base-classes that can not be directly inheritable
    Args:
        DeclarativeBase (_type_): Base Class for SqlAlchemy ORM
        MappedAsDataclass (_type_): Base Class for SqlAlchemy ORM
    """

    pass


class ResourceTypes(AlmaTable):
    """The extension class for Table ORM Model in SqlAlchemy::ORM module
    Args:
        AlmaTable (_type_): The Mix-In Class of two SqlAlchemy ORM base-classes that can't be directly inheritable
    Returns:
        _type_: ResourceTypes ORM model of the resource_types table in the underlying DB
    """

    __tablename__ = "resource_types"
    resource_type: Mapped[text_] = mapped_column(nullable=False, primary_key=True)
    # -------------------------------------------------------------------------

    def __repr__(self):
        return f"{self.resource_type}"

    # -------------------------------------------------------------------------


def execute_in_session(statement) -> CursorResult | None:
    """Reusable function to Execute SQL-Alchemy statement in a session
    Args:
        statement (_type_): _description_
    """
    result = None
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)
    with Session() as session:
        result = session.execute(statement)
        session.commit()
    # pprint(f'{dir(result)=}')
    return result
    # -----------------------------------------------------------------------------


def upgrade():
    """Alembic Upgrade Hook-Point that deletes the entry from
    resource_types table with value 'resource_snapshot'
    """
    delete_statement = (
        # Upgrade means death.
        # Death of the 'resource_snapshot'
        # resource_type row entry
        delete(ResourceTypes).where(ResourceTypes.resource_type == "resource_snapshot")
    )
    execute_in_session(delete_statement)
    # -----------------------------------------------------------------------------


def downgrade():
    """Alembic Downgrade Hook-Point that reinstates the entry to
    resource_types table with value 'resource_snapshot'
    """
    ### Generic SQL INSERT (!!! particularly psql dialect !!!) doesn't have
    ### .on_conflict_do_nothing(index_elements=['resource_type'])
    ### Fixing 'Insert' object has no attribute 'on_conflict_do_nothing'
    select_statement = select(ResourceTypes).where(
        ResourceTypes.resource_type == "resource_snapshot"
    )
    result = execute_in_session(select_statement)
    ### Brutal, forceful, but more efficient that highly discouraged func.count in query
    ### Unfortunately it is required to assure we don't end up with table
    ### containing multiple resource_snapshot rows
    count = 0
    if result:
        for row in result:
            count += 1
    # Done counting: if not 0 ignore
    if not result or count == 0:
        insert_statement = (
            # Downgrade means rebirth.
            # Rebirth of the 'resource_snapshot'
            # resource_type row entry
            insert(ResourceTypes).values(resource_type="resource_snapshot")
        )
        execute_in_session(insert_statement)
    # -----------------------------------------------------------------------------
