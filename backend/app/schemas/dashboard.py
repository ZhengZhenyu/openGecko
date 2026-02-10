"""
Dashboard (个人工作台) Schemas
"""
from datetime import datetime
from typing import List, Optional, Literal
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
    scheduled_at: Optional[datetime] = None
    assignee_count: int
    creator_name: Optional[str] = None


class WorkStatusStats(BaseModel):
    """工作状态统计"""
    planning: int = 0
    in_progress: int = 0
    completed: int = 0


class DashboardResponse(BaseModel):
    """个人工作台响应"""
    contents: List[AssignedItem]
    meetings: List[AssignedItem]
    content_stats: WorkStatusStats
    meeting_stats: WorkStatusStats
    total_assigned_items: int


class UpdateWorkStatusRequest(BaseModel):
    """更新工作状态请求"""
    work_status: Literal["planning", "in_progress", "completed"]


class AssigneeCreate(BaseModel):
    """添加责任人请求"""
    user_ids: List[int]


class AssigneeResponse(BaseModel):
    """责任人响应"""
    id: int
    username: str
    full_name: str
    email: str
    assigned_at: datetime
