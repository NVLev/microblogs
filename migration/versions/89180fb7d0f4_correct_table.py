"""correct table

Revision ID: 89180fb7d0f4
Revises: b8a3e3a6be98
Create Date: 2024-11-11 21:58:32.870089

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = "89180fb7d0f4"
down_revision: Union[str, None] = "b8a3e3a6be98"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_unique_constraint(
        "unique_follow_relationship", "follow", ["follower_id", "following_id"]
    )



def downgrade() -> None:

    op.drop_constraint("unique_follow_relationship", "follow", type_="unique")

