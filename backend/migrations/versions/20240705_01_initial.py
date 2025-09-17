"""Initial schema for presets, logs, and hardware profiles."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20240705_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create base tables."""

    op.create_table(
        "category",
        sa.Column("id", sa.String(length=255), primary_key=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
    )
    op.create_table(
        "preset",
        sa.Column("id", sa.String(length=255), primary_key=True),
        sa.Column("category", sa.String(length=255), sa.ForeignKey("category.id"), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("mod_rate_hz", sa.Float(), nullable=True),
        sa.Column("duty_cycle", sa.Float(), nullable=True),
        sa.Column("depth", sa.Float(), nullable=True),
        sa.Column("window_ms", sa.Float(), nullable=True),
        sa.Column("carrier_type", sa.String(length=255), nullable=True),
        sa.Column("carrier_hz", sa.Float(), nullable=True),
        sa.Column("outer_envelope_rate", sa.Float(), nullable=True),
        sa.Column("outer_envelope_depth", sa.Float(), nullable=True),
        sa.Column("phase_options_deg", sa.JSON(), nullable=True),
        sa.Column("duration_minutes", sa.Float(), nullable=True),
        sa.Column("visual_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("visual_rate_hz", sa.Float(), nullable=True),
        sa.Column("visual_phase_deg", sa.Float(), nullable=True),
        sa.Column("precision_note", sa.String(length=512), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
        sa.Column("mechanism", sa.Text(), nullable=True),
        sa.Column("expected_effects", sa.Text(), nullable=False, server_default=""),
        sa.Column("audio_config", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("visual_config", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("safety_label", sa.String(length=255), nullable=True),
        sa.Column("safety_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("safety_config", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("max_volume_pct", sa.Integer(), nullable=True),
        sa.Column("photosensitivity_flag", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("citations", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.create_table(
        "sessionlog",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("preset_id", sa.String(length=255), sa.ForeignKey("preset.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("effective_hz", sa.Float(), nullable=True),
        sa.Column("jitter_p95_ms", sa.Float(), nullable=True),
        sa.Column("jitter_p99_ms", sa.Float(), nullable=True),
        sa.Column("dropped_frames", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("raw_path", sa.String(length=512), nullable=True),
    )
    op.create_index("ix_sessionlog_started_at", "sessionlog", ["started_at"], unique=False)
    op.create_table(
        "hardwareprofile",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_guid", sa.String(length=255), nullable=False),
        sa.Column("friendly_name", sa.String(length=255), nullable=False),
        sa.Column("form_factor", sa.String(length=255), nullable=True),
        sa.Column("mix_format", sa.String(length=255), nullable=True),
        sa.Column("mtf_pass_hz", sa.Float(), nullable=True),
        sa.Column("mtf_scores", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("latency_jitter_ms", sa.Float(), nullable=True),
        sa.Column("tested_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_hardwareprofile_device_guid", "hardwareprofile", ["device_guid"], unique=False)
    op.create_index("ix_hardwareprofile_tested_at", "hardwareprofile", ["tested_at"], unique=False)


def downgrade() -> None:
    """Drop base tables."""

    op.drop_index("ix_hardwareprofile_tested_at", table_name="hardwareprofile")
    op.drop_index("ix_hardwareprofile_device_guid", table_name="hardwareprofile")
    op.drop_table("hardwareprofile")
    op.drop_index("ix_sessionlog_started_at", table_name="sessionlog")
    op.drop_table("sessionlog")
    op.drop_table("preset")
    op.drop_table("category")
