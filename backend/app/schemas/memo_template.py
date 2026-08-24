from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MemoFieldType


class MemoTemplateFieldCreate(BaseModel):
    label: str
    field_type: MemoFieldType
    max_length: int | None = None
    order_index: int = 0
    required: bool = True


class MemoTemplateFieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    field_type: MemoFieldType
    max_length: int | None
    order_index: int
    required: bool


class MemoApprovalStepCreate(BaseModel):
    step_order: int
    approver_id: int
    deadline_hours: int = Field(gt=0)


class MemoApprovalStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    step_order: int
    approver_id: int
    deadline_hours: int


class MemoTemplateCreate(BaseModel):
    name: str
    fields: list[MemoTemplateFieldCreate]
    approval_steps: list[MemoApprovalStepCreate]


class MemoTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    is_active: bool
    fields: list[MemoTemplateFieldOut]
    approval_steps: list[MemoApprovalStepOut]
