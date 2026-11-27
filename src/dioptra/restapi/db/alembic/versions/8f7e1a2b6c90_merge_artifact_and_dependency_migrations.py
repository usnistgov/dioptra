"""Merge artifact storage and resource dependency migrations.

Revision ID: 8f7e1a2b6c90
Revises: c4e1c2004f14, c587fd9d0aff
"""

revision = "8f7e1a2b6c90"
down_revision = ("c4e1c2004f14", "c587fd9d0aff")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Join the independent migration branches."""
    pass


def downgrade() -> None:
    """Restore the independent branch heads."""
    pass
