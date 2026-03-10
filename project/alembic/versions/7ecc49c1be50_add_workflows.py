"""add workflows

Revision ID: 7ecc49c1be50
Revises: 
Create Date: 2024-01-01
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "7ecc49c1be50"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("patients") as batch_op:
        batch_op.create_unique_constraint(
            "uq_patients_patient_id",
            ["patient_id"]
        )

    op.create_table(
        "workflows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("definition", sa.String(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
    )


def downgrade():
    with op.batch_alter_table("patients") as batch_op:
        batch_op.drop_constraint("uq_patients_patient_id", type_="unique")

    op.drop_table("workflows")
