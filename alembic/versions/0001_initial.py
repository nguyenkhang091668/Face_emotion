"""Initial migration — create all tables."""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    #  permissions 
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
    )

    #  roles 
    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
    )

    #  users 
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True,
                  nullable=False, index=True),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("is_superuser", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )

    #  user_roles (M2M) 
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(36), sa.ForeignKey(
            "users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.String(36), sa.ForeignKey(
            "roles.id", ondelete="CASCADE"), primary_key=True),
    )

    #  role_permissions (M2M) 
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.String(36), sa.ForeignKey(
            "roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", sa.String(36), sa.ForeignKey(
            "permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    #  refresh_tokens 
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("token", sa.String(512), unique=True,
                  nullable=False, index=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey(
            "users.id", ondelete="CASCADE")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )

    #  detection_sessions 
    op.create_table(
        "detection_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey(
            "users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("started_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("frame_count", sa.Integer, default=0),
    )

    #  emotion_logs 
    op.create_table(
        "emotion_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey(
            "detection_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), index=True),
        sa.Column("dominant_emotion", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("scores", sa.JSON, nullable=True),
        sa.Column("face_box", sa.JSON, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("emotion_logs")
    op.drop_table("detection_sessions")
    op.drop_table("refresh_tokens")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("permissions")
