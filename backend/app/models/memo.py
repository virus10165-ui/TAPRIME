from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import ApprovalStepStatus, MemoStatus


class Memo(Base):
    """Конкретная служебная записка, созданная сотрудником по одному из шаблонов."""

    __tablename__ = "memos"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("memo_templates.id", ondelete="RESTRICT"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    status: Mapped[MemoStatus] = mapped_column(nullable=False, default=MemoStatus.PENDING)
    # Номер текущего активного шага согласования; None когда записка полностью
    # согласована или отклонена (согласование завершено).
    current_step_order: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Значения полей шаблона: {"<template_field_id>": <значение>}.
    # Текст -> строка, число -> число, валюта -> {"amount": число, "currency": "KZT"}.
    values: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    steps: Mapped[list["MemoApprovalStep"]] = relationship(
        back_populates="memo", cascade="all, delete-orphan", order_by="MemoApprovalStep.step_order"
    )


class MemoApprovalStep(Base):
    """Шаг согласования конкретной записки — снимок шага шаблона на момент
    создания записки, плюс фактическое состояние (когда стал активным, дедлайн,
    решение)."""

    __tablename__ = "memo_approval_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    memo_id: Mapped[int] = mapped_column(ForeignKey("memos.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    approver_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    deadline_hours: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[ApprovalStepStatus] = mapped_column(nullable=False, default=ApprovalStepStatus.WAITING)

    # Заполняются, когда шаг становится активным (наступает его очередь)
    became_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Просрочка: как только became_active_at + deadline_hours прошёл, а решения
    # ещё нет — ставим is_overdue=True и шлём оповещение один раз (overdue_notified_at).
    # deadline_at при этом НЕ сдвигается — счётчик «уходит в минус» естественным
    # образом как (now - deadline_at) для отчётов.
    is_overdue: Mapped[bool] = mapped_column(default=False, nullable=False)
    overdue_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    memo: Mapped["Memo"] = relationship(back_populates="steps")
