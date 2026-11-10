"""Bring the schema up to the models on main; unique indexes that ignore NULLs.

SQL Server treats NULLs as equal in a UNIQUE constraint and won't alter a column
a UNIQUE constraint depends on, so those constraints are dropped first and
replaced by filtered unique indexes.

Revision ID: a1c0d2e3f4a5
Revises: 18497563da61
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1c0d2e3f4a5"
down_revision: Union[str, Sequence[str], None] = "18497563da61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ORCID = sa.String(length=19)
_UNIQUE_CONSTRAINTS = sa.text(
    """
    SELECT kc.name
    FROM sys.key_constraints kc
    JOIN sys.index_columns ic ON ic.object_id = kc.parent_object_id AND ic.index_id = kc.unique_index_id
    JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
    WHERE kc.type = 'UQ' AND kc.parent_object_id = OBJECT_ID(:table) AND c.name = :column
    """
)
# New required columns with no value that could honestly be filled in for old rows.
_REQUIRES_EMPTY = ("researchers", "form_questions", "publication_resources")


def _drop_unique_constraint(table: str, column: str) -> None:
    names = op.get_bind().execute(_UNIQUE_CONSTRAINTS, {"table": table, "column": column}).scalars().all()
    for name in names:
        op.drop_constraint(name, table, type_="unique")


def upgrade() -> None:
    bind = op.get_bind()
    for table in _REQUIRES_EMPTY:
        if bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError(
                f"{table} has rows, but this migration adds required columns with no safe default "
                "(researchers.email, form_questions.criticality_question_id, publication_resources.criticality). "
                "Empty those tables or give them defaults in this migration before upgrading."
            )

    _drop_unique_constraint("form_batches", "google_form_id")
    op.create_index(
        "uq_form_batches_google_form_id", "form_batches", ["google_form_id"],
        unique=True, mssql_where=sa.text("google_form_id IS NOT NULL"),
    )
    op.add_column("form_batches", sa.Column("researcher_id", sa.Integer(), nullable=True))
    op.add_column("form_batches", sa.Column("invitation_to", sa.String(length=320), nullable=True))
    op.add_column("form_batches", sa.Column("invitation_sent_at", sa.DateTime(), nullable=True))
    op.create_foreign_key("fk_form_batches_researcher_id", "form_batches", "researchers", ["researcher_id"], ["id"])

    op.add_column("form_questions", sa.Column("criticality_question_id", sa.String(length=255), nullable=False))
    op.add_column("form_questions", sa.Column("usage_answer", sa.String(length=10), nullable=True))
    op.add_column("form_questions", sa.Column("other_resource_text", sa.String(length=2000), nullable=True))
    op.add_column("form_questions", sa.Column("reported_criticality", sa.String(length=20), nullable=True))
    op.add_column("publication_resources", sa.Column("criticality", sa.String(length=20), nullable=False))

    op.add_column("publications", sa.Column("first_discovered_researcher_id", sa.Integer(), nullable=True))
    op.alter_column("publications", "first_discovered_by_orcid", existing_type=_ORCID, nullable=True)
    op.create_index(
        op.f("ix_publications_first_discovered_researcher_id"), "publications", ["first_discovered_researcher_id"]
    )
    op.create_foreign_key(
        "fk_publications_first_discovered_researcher_id", "publications", "researchers",
        ["first_discovered_researcher_id"], ["id"],
    )

    op.add_column("researchers", sa.Column("email", sa.String(length=320), nullable=False))
    _drop_unique_constraint("researchers", "orcid")
    op.alter_column("researchers", "orcid", existing_type=_ORCID, nullable=True)
    op.create_index(
        "uq_researchers_orcid", "researchers", ["orcid"], unique=True, mssql_where=sa.text("orcid IS NOT NULL")
    )


def downgrade() -> None:
    op.drop_index("uq_researchers_orcid", table_name="researchers")
    op.alter_column("researchers", "orcid", existing_type=_ORCID, nullable=False)
    op.create_unique_constraint("uq_researchers_orcid", "researchers", ["orcid"])
    op.drop_column("researchers", "email")

    op.drop_constraint("fk_publications_first_discovered_researcher_id", "publications", type_="foreignkey")
    op.drop_index(op.f("ix_publications_first_discovered_researcher_id"), table_name="publications")
    op.alter_column("publications", "first_discovered_by_orcid", existing_type=_ORCID, nullable=False)
    op.drop_column("publications", "first_discovered_researcher_id")

    op.drop_column("publication_resources", "criticality")
    op.drop_column("form_questions", "reported_criticality")
    op.drop_column("form_questions", "other_resource_text")
    op.drop_column("form_questions", "usage_answer")
    op.drop_column("form_questions", "criticality_question_id")

    op.drop_constraint("fk_form_batches_researcher_id", "form_batches", type_="foreignkey")
    op.drop_column("form_batches", "invitation_sent_at")
    op.drop_column("form_batches", "invitation_to")
    op.drop_column("form_batches", "researcher_id")
    op.drop_index("uq_form_batches_google_form_id", table_name="form_batches")
    op.create_unique_constraint("uq_form_batches_google_form_id", "form_batches", ["google_form_id"])
