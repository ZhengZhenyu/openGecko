"""
Dashboard (个人工作台) Schemas
"""
from datetime import date, datetime
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


class AssignedEventTask(BaseModel):
    """分配给用户的活动任务"""
    id: int
    type: Literal["event_task"] = "event_task"
    title: str
    task_type: str        # task / milestone
    phase: str            # pre / during / post
    status: str           # not_started / in_progress / completed / blocked
    start_date: date | None = None
    end_date: date | None = None
    progress: int = 0
    event_id: int
    event_title: str | None = None


class AssignedChecklistItem(BaseModel):
    """分配给用户的活动清单项"""
    id: int
    type: Literal["checklist_item"] = "checklist_item"
    title: str
    phase: str            # pre / during / post
    status: str           # pending / done / skipped
    due_date: date | None = None
    event_id: int
    event_title: str | None = None


class AssignedCampaignTask(BaseModel):
    """分配给用户的运营活动任务"""
    id: int
    type: Literal["campaign_task"] = "campaign_task"
    title: str
    status: str           # not_started / in_progress / completed / blocked
    priority: str         # low / medium / high
    deadline: date | None = None
    campaign_id: int
    campaign_name: str | None = None


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
    event_tasks: list[AssignedEventTask] = []
    checklist_items: list[AssignedChecklistItem] = []
    campaign_tasks: list[AssignedCampaignTask] = []
    content_stats: WorkStatusStats
    meeting_stats: WorkStatusStats
    event_task_stats: WorkStatusStats = WorkStatusStats()
    checklist_item_stats: WorkStatusStats = WorkStatusStats()
    campaign_task_stats: WorkStatusStats = WorkStatusStats()
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
    event_task_stats: WorkStatusStats = WorkStatusStats()
    checklist_item_stats: WorkStatusStats = WorkStatusStats()
    campaign_task_stats: WorkStatusStats = WorkStatusStats()
    content_by_type: ContentByTypeStats
    total: int


class WorkloadOverviewResponse(BaseModel):
    """工作量总览响应"""
    users: list[UserWorkloadItem]
