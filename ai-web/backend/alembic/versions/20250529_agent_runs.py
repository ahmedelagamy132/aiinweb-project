"""Add agent_runs table for persisting agent execution history.

Revision ID: 20250529_agent_runs
Revises: 20250212_initial
Create Date: 2025-05-29
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20250529_agent_runs"
down_revision: Union[str, None] = "20250212_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("feature_slug", sa.String(length=120), nullable=False),
        sa.Column("audience_role", sa.String(length=120), nullable=False),
        sa.Column("audience_experience", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("gemini_insight", sa.Text(), nullable=True),
        sa.Column("recommended_actions", postgresql.JSONB(), nullable=False),
        sa.Column("tool_calls", postgresql.JSONB(), nullable=False),
        sa.Column("rag_contexts", postgresql.JSONB(), nullable=False),
        sa.Column("used_gemini", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_runs_feature_slug"),
        "agent_runs",
        ["feature_slug"],
        unique=False,
    )

    # Seed feature-related document chunks for RAG to help the agent
    conn = op.get_bind()
    seed_data = [
        {
            "slug": "release-readiness",
            "source": "docs/agent",
            "content": "The release readiness agent evaluates feature launches by analyzing "
                       "launch windows, stakeholder contacts, and SLO requirements. It provides "
                       "actionable recommendations for successful product releases.",
        },
        {
            "slug": "curriculum-pathways",
            "source": "features/curriculum",
            "content": "Curriculum Pathways helps instructors create sequenced lab recommendations "
                       "based on student progress and prior completions. It targets intermediate "
                       "instructors and aims for 90% adoption rate.",
        },
        {
            "slug": "team-analytics",
            "source": "features/analytics",
            "content": "Team Analytics Dashboard provides consolidated insights on agent usage "
                       "and completion trends. Designed for Program Managers with advanced "
                       "experience levels, targeting 25% increase in daily active users.",
        },
    ]

    for entry in seed_data:
        conn.execute(
            sa.text(
                """
                INSERT INTO document_chunks (slug, source, content, embedding, created_at)
                VALUES (:slug, :source, :content, '[]'::jsonb, now())
                """
            ),
            entry,
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_runs_feature_slug"), table_name="agent_runs")
    op.drop_table("agent_runs")
    # Note: We don't remove the seeded document_chunks as they may be used elsewhere
