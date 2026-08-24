from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApprovalStepStatus, MemoStatus


class MemoCreate(BaseModel):
    template_id: int
    # {"<template_field_id>": значение}
    values: dict


class MemoApprovalStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    step_order: int
    approver_id: int
    status: ApprovalStepStatus
    became_active_at: datetime | None
    deadline_at: datetime | None
    decided_at: datetime | None
    comment: str | None
    is_overdue: bool


class MemoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    template_id: int
    author_id: int
    status: MemoStatus
    current_step_order: int | None
    values: dict
    created_at: datetime
    decided_at: datetime | None
    steps: list[MemoApprovalStepOut]


class MemoDecisionRequest(BaseModel):
    approve: bool
    comment: str | None = None
