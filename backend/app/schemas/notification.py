from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    body: str | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime
    resource_type: str | None
    resource_id: int | None

    model_config = ConfigDict(from_attributes=True)


class NotificationListOut(BaseModel):
    items: list[NotificationOut]
    total: int
    unread_count: int
