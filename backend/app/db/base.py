"""Импортирует все модели, чтобы Base.metadata видела их для Alembic autogenerate."""

from app.db.base_class import Base  # noqa: F401
from app.models import Company, Department, User  # noqa: F401
