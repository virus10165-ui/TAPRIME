"""memo templates, memos, approval steps, notifications

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

memo_field_type_enum = sa.Enum("text", "number", "currency", name="memofieldtype")
memo_status_enum = sa.Enum("pending", "approved", "rejected", name="memostatus")
approval_step_status_enum = sa.Enum("waiting", "pending", "approved", "rejected", name="approvalstepstatus")
notification_type_enum = sa.Enum("approval_needed", "overdue", "decided", name="notificationtype")


def upgrade() -> None:
    bind = op.get_bind()
    memo_field_type_enum.create(bind, checkfirst=True)
    memo_status_enum.create(bind, checkfirst=True)
    approval_step_status_enum.create(bind, checkfirst=True)
    notification_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "memo_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_memo_templates_company_id", "memo_templates", ["company_id"])

    op.create_table(
        "memo_template_fields",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "template_id", sa.Integer(), sa.ForeignKey("memo_templates.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("field_type", memo_field_type_enum, nullable=False),
        sa.Column("max_length", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_memo_template_fields_template_id", "memo_template_fields", ["template_id"])

    op.create_table(
        "memo_approval_step_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "template_id", sa.Integer(), sa.ForeignKey("memo_templates.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("approver_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("deadline_hours", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_memo_approval_step_templates_template_id", "memo_approval_step_templates", ["template_id"]
    )

    op.create_table(
        "memos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "template_id", sa.Integer(), sa.ForeignKey("memo_templates.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", memo_status_enum, nullable=False, server_default="pending"),
        sa.Column("current_step_order", sa.Integer(), nullable=True),
        sa.Column("values", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_memos_company_id", "memos", ["company_id"])

    op.create_table(
        "memo_approval_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("memo_id", sa.Integer(), sa.ForeignKey("memos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("approver_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("deadline_hours", sa.Integer(), nullable=False),
        sa.Column("status", approval_step_status_enum, nullable=False, server_default="waiting"),
        sa.Column("became_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("is_overdue", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("overdue_notified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_memo_approval_steps_memo_id", "memo_approval_steps", ["memo_id"])
    op.create_index("ix_memo_approval_steps_approver_id", "memo_approval_steps", ["approver_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("memo_id", sa.Integer(), sa.ForeignKey("memos.id", ondelete="CASCADE"), nullable=True),
        sa.Column("type", notification_type_enum, nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_memo_approval_steps_approver_id", table_name="memo_approval_steps")
    op.drop_index("ix_memo_approval_steps_memo_id", table_name="memo_approval_steps")
    op.drop_table("memo_approval_steps")

    op.drop_index("ix_memos_company_id", table_name="memos")
    op.drop_table("memos")

    op.drop_index("ix_memo_approval_step_templates_template_id", table_name="memo_approval_step_templates")
    op.drop_table("memo_approval_step_templates")

    op.drop_index("ix_memo_template_fields_template_id", table_name="memo_template_fields")
    op.drop_table("memo_template_fields")

    op.drop_index("ix_memo_templates_company_id", table_name="memo_templates")
    op.drop_table("memo_templates")

    bind = op.get_bind()
    notification_type_enum.drop(bind, checkfirst=True)
    approval_step_status_enum.drop(bind, checkfirst=True)
    memo_status_enum.drop(bind, checkfirst=True)
    memo_field_type_enum.drop(bind, checkfirst=True)
