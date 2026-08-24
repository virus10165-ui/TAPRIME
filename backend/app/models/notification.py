from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.enums import NotificationType


class Notification(Base):
    """Внутриплатформенное уведомление пользователю. В Phase 1 — только
    внутренние (видны в GET /notifications); отправка email/SMS — Phase 4,
    когда определимся с провайдером."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    memo_id: Mapped[int | None] = mapped_column(ForeignKey("memos.id", ondelete="CASCADE"), nullable=True)
    type: Mapped[NotificationType] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
