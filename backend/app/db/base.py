"""Импортирует все модели, чтобы Base.metadata видела их для Alembic autogenerate."""

from app.db.base_class import Base  # noqa: F401
from app.models import (  # noqa: F401
    Company,
    Department,
    Memo,
    MemoApprovalStep,
    MemoApprovalStepTemplate,
    MemoTemplate,
    MemoTemplateField,
    Notification,
    User,
)
