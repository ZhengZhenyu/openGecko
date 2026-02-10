from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ContentCreate(BaseModel):
    title: str
    content_markdown: str = ""
    source_type: str = "contribution"
    author: str = ""
    tags: list[str] = []
    category: str = ""
    cover_image: Optional[str] = None
    scheduled_publish_at: Optional[datetime] = None


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    content_markdown: Optional[str] = None
    content_html: Optional[str] = None
    source_type: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[list[str]] = None
    category: Optional[str] = None
    cover_image: Optional[str] = None
    scheduled_publish_at: Optional[datetime] = None


class ContentStatusUpdate(BaseModel):
    status: str


class ContentOut(BaseModel):
    id: int
    title: str
    content_markdown: str
    content_html: str
    source_type: str
    source_file: Optional[str]
    author: str
    tags: list[str]
    category: str
    cover_image: Optional[str]
    status: str
    community_id: int
    created_by_user_id: Optional[int]
    owner_id: Optional[int]
    scheduled_publish_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContentListOut(BaseModel):
    id: int
    title: str
    source_type: str
    author: str
    tags: list[str]
    category: str
    status: str
    owner_id: Optional[int] = None
    scheduled_publish_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContentCalendarOut(BaseModel):
    """日历视图专用的轻量响应模型"""
    id: int
    title: str
    status: str
    source_type: str
    author: str
    category: str
    scheduled_publish_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentScheduleUpdate(BaseModel):
    """拖拽更新发布时间"""
    scheduled_publish_at: Optional[datetime] = None


class PaginatedContents(BaseModel):
    items: list[ContentListOut]
    total: int
    page: int
    page_size: int
