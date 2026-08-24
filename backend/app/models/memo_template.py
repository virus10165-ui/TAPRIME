from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import MemoFieldType


class MemoTemplate(Base):
    """Вид служебной записки. Настраивается администратором компании:
    свой набор полей (MemoTemplateField) и своя цепочка согласования
    (MemoApprovalStepTemplate)."""

    __tablename__ = "memo_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    fields: Mapped[list["MemoTemplateField"]] = relationship(
        back_populates="template", cascade="all, delete-orphan", order_by="MemoTemplateField.order_index"
    )
    approval_steps: Mapped[list["MemoApprovalStepTemplate"]] = relationship(
        back_populates="template", cascade="all, delete-orphan", order_by="MemoApprovalStepTemplate.step_order"
    )


class MemoTemplateField(Base):
    """Одно поле шаблона (конструктор полей)."""

    __tablename__ = "memo_template_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("memo_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[MemoFieldType] = mapped_column(nullable=False)
    max_length: Mapped[int | None] = mapped_column(Integer, nullable=True)  # только для текстовых полей
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    template: Mapped["MemoTemplate"] = relationship(back_populates="fields")


class MemoApprovalStepTemplate(Base):
    """Шаг цепочки согласования в шаблоне: кто согласует на этом шаге и сколько
    часов у него есть, прежде чем шаг станет просроченным. При создании
    конкретной записки эта цепочка «снимается копией» в MemoApprovalStep,
    чтобы последующие правки шаблона не меняли задним числом уже идущие записки."""

    __tablename__ = "memo_approval_step_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("memo_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    approver_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    deadline_hours: Mapped[int] = mapped_column(Integer, nullable=False)

    template: Mapped["MemoTemplate"] = relationship(back_populates="approval_steps")
