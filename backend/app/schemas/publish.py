from datetime import datetime

from pydantic import BaseModel


class PublishRequest(BaseModel):
    thumb_media_id: str = ""


class PublishRecordOut(BaseModel):
    id: int
    content_id: int
    channel: str
    status: str
    platform_article_id: str | None
    platform_url: str | None
    published_at: datetime | None
    error_message: str | None
    created_at: datetime
    community_id: int

    model_config = {"from_attributes": True}


class PublishRecordListOut(BaseModel):
    total: int
    items: list[PublishRecordOut]


class ChannelPreview(BaseModel):
    channel: str
    title: str
    content: str
    format: str  # "html" or "markdown"


class CopyContent(BaseModel):
    channel: str
    title: str
    content: str
    format: str
    platform: str


class AnalyticsOut(BaseModel):
    id: int
    publish_record_id: int
    read_count: int
    like_count: int
    share_count: int
    comment_count: int
    collected_at: datetime

    model_config = {"from_attributes": True}


class AnalyticsOverview(BaseModel):
    total_contents: int
    total_published: int
    channels: dict[str, int]  # channel -> published count


class ContentAnalyticsDetail(BaseModel):
    """内容分析详情（含发布记录列表）"""
    content_id: int
    title: str
    analytics: list["PublishRecordOut"] = []

    model_config = {"from_attributes": True}


class ChannelConfigOut(BaseModel):
    id: int
    channel: str
    config: dict
    enabled: bool

    model_config = {"from_attributes": True}


class ChannelConfigCreate(BaseModel):
    channel: str  # wechat, hugo, csdn, zhihu, ...
    config: dict = {}
    enabled: bool = False


class ChannelConfigUpdate(BaseModel):
    config: dict = {}
    enabled: bool | None = None
