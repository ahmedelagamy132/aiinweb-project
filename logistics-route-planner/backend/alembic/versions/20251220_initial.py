"""Initial migration for Logistics Route Planner.

Revision ID: 20251220_initial
Revises:
Create Date: 2025-12-20

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251220_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create echo_attempts table
    op.create_table(
        "echo_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_key", sa.String(length=255), nullable=False),
        sa.Column("failures", sa.Integer(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_echo_attempts_client_key"), "echo_attempts", ["client_key"], unique=False)

    # Create route_runs table
    op.create_table(
        "route_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("goal", sa.String(length=255), nullable=False),
        sa.Column("audience_role", sa.String(length=120), nullable=False),
        sa.Column("audience_experience", sa.String(length=32), nullable=False),
        sa.Column("primary_risk", sa.String(length=255), nullable=True),
        sa.Column("include_risks", sa.Boolean(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("plan", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create document_chunks table
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_chunks_slug"), "document_chunks", ["slug"], unique=False)

    # Create agent_runs table
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("route_slug", sa.String(length=120), nullable=False),
        sa.Column("audience_role", sa.String(length=120), nullable=False),
        sa.Column("audience_experience", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("gemini_insight", sa.Text(), nullable=True),
        sa.Column("recommended_actions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tool_calls", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rag_contexts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("used_gemini", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_runs_route_slug"), "agent_runs", ["route_slug"], unique=False)

    # Seed sample document chunks for RAG
    op.execute("""
        INSERT INTO document_chunks (slug, source, content, created_at) VALUES
        ('logistics-best-practices', 'Logistics Handbook', 'Route optimization should consider traffic patterns, delivery windows, and vehicle capacity. Always verify delivery addresses before dispatch and maintain communication with drivers.', NOW()),
        ('delivery-windows', 'Delivery Guidelines', 'Delivery windows should be set based on customer availability and traffic conditions. Morning deliveries (6AM-10AM) typically have less traffic. Afternoon slots (2PM-6PM) may need buffer time for traffic.', NOW()),
        ('risk-mitigation', 'Risk Management Guide', 'Common logistics risks include vehicle breakdowns, traffic delays, and incorrect addresses. Mitigation strategies: maintain backup vehicles, plan alternative routes, and verify addresses 24 hours before delivery.', NOW()),
        ('driver-safety', 'Safety Protocols', 'Driver safety is paramount. Ensure regular breaks every 2 hours, avoid driving during adverse weather conditions, and always use GPS navigation. Report any safety concerns immediately.', NOW()),
        ('fuel-efficiency', 'Operations Manual', 'Optimize fuel efficiency by planning routes that minimize left turns, avoiding peak traffic hours, and maintaining proper tire pressure. Regular vehicle maintenance reduces fuel consumption by up to 15%.', NOW())
    """)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_runs_route_slug"), table_name="agent_runs")
    op.drop_table("agent_runs")
    op.drop_index(op.f("ix_document_chunks_slug"), table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_table("route_runs")
    op.drop_index(op.f("ix_echo_attempts_client_key"), table_name="echo_attempts")
    op.drop_table("echo_attempts")
