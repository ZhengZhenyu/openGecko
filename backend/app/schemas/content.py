from datetime import datetime

from pydantic import BaseModel


class ContentCreate(BaseModel):
    title: str
    content_markdown: str = ""
    content_html: str = ""
    source_type: str = "contribution"
    author: str = ""
    tags: list[str] = []
    category: str = ""
    cover_image: str | None = None
    scheduled_publish_at: datetime | None = None
    work_status: str = "planning"
    assignee_ids: list[int] = []
    # 多社区关联：不填则默认使用 X-Community-Id header 对应的社区
    community_ids: list[int] = []


class ContentUpdate(BaseModel):
    title: str | None = None
    content_markdown: str | None = None
    content_html: str | None = None
    source_type: str | None = None
    author: str | None = None
    tags: list[str] | None = None
    category: str | None = None
    cover_image: str | None = None
    scheduled_publish_at: datetime | None = None
    work_status: str | None = None
    assignee_ids: list[int] | None = None
    # 多社区关联：提供则替换全部关联；不提供则不变
    community_ids: list[int] | None = None


class ContentStatusUpdate(BaseModel):
    status: str


class ContentOut(BaseModel):
    id: int
    title: str
    content_markdown: str
    content_html: str
    source_type: str
    source_file: str | None
    author: str
    tags: list[str]
    category: str
    cover_image: str | None
    status: str
    work_status: str
    community_id: int | None
    created_by_user_id: int | None
    owner_id: int | None
    scheduled_publish_at: datetime | None
    created_at: datetime
    updated_at: datetime
    assignee_ids: list[int] = []
    # 多社区关联列表（由 API 层手动填充）
    community_ids: list[int] = []

    model_config = {"from_attributes": True}


class ContentListOut(BaseModel):
    id: int
    title: str
    source_type: str
    author: str
    tags: list[str]
    category: str
    status: str
    owner_id: int | None = None
    scheduled_publish_at: datetime | None = None
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
    scheduled_publish_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentScheduleUpdate(BaseModel):
    """拖拽更新发布时间"""
    scheduled_publish_at: datetime | None = None


class PaginatedContents(BaseModel):
    items: list[ContentListOut]
    total: int
    page: int
    page_size: int
