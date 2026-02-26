"""
Dashboard (个人工作台) Schemas
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AssignedItem(BaseModel):
    """分配给用户的工作项（内容或会议）"""
    id: int
    type: Literal["content", "meeting"]
    title: str
    work_status: str  # planning, in_progress, completed
    status: str  # 原有的状态字段（draft/published 或 scheduled/completed）
    created_at: datetime
    updated_at: datetime
    scheduled_at: datetime | None = None
    assignee_count: int
    creator_name: str | None = None


class WorkStatusStats(BaseModel):
    """工作状态统计"""
    planning: int = 0
    in_progress: int = 0
    completed: int = 0
    overdue: int = 0  # 未完成且截止日已过


class DashboardResponse(BaseModel):
    """个人工作台响应"""
    contents: list[AssignedItem]
    meetings: list[AssignedItem]
    content_stats: WorkStatusStats
    meeting_stats: WorkStatusStats
    total_assigned_items: int


class UpdateWorkStatusRequest(BaseModel):
    """更新工作状态请求"""
    work_status: Literal["planning", "in_progress", "completed"]


class AssigneeCreate(BaseModel):
    """添加责任人请求"""
    user_ids: list[int]


class AssigneeResponse(BaseModel):
    """责任人响应"""
    id: int
    username: str
    full_name: str
    email: str
    assigned_at: datetime


class ContentByTypeStats(BaseModel):
    """按内容类型统计"""
    contribution: int = 0
    release_note: int = 0
    event_summary: int = 0


class UserWorkloadItem(BaseModel):
    """单个用户的工作量数据"""
    user_id: int
    username: str
    full_name: str | None = None
    content_stats: WorkStatusStats
    meeting_stats: WorkStatusStats
    content_by_type: ContentByTypeStats
    total: int


class WorkloadOverviewResponse(BaseModel):
    """工作量总览响应"""
    users: list[UserWorkloadItem]
