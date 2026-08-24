from datetime import datetime

from pydantic import BaseModel


class OverdueStepOut(BaseModel):
    memo_id: int
    step_order: int
    approver_id: int
    deadline_at: datetime
    overdue_hours: float
