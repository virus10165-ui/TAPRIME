from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationType


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    memo_id: int | None
    type: NotificationType
    message: str
    created_at: datetime
    read_at: datetime | None
