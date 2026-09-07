"""Stable pagination and local-profile date filtering index."""

from alembic import op

revision = "desktop_002"
down_revision = "desktop_001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_transactions_profile_date", "transactions", ["user_id", "transaction_date", "id"])


def downgrade():
    op.drop_index("ix_transactions_profile_date", table_name="transactions")
