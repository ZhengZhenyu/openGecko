"""
个人工作台 API - 用户视角的统一视图
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, get_current_community
from app.models.user import User
from app.models.content import Content
from app.models.meeting import Meeting
from app.schemas.dashboard import (
    DashboardResponse,
    AssignedItem,
    WorkStatusStats,
    UpdateWorkStatusRequest,
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取用户个人工作台数据（跨所有社区）
    包括：
    - 我负责的内容（assigned_contents）
    - 我负责的会议（assigned_meetings）
    - 工作状态统计
    """
    
    # 获取我负责的内容（所有社区）
    assigned_contents = (
        db.query(Content)
        .join(Content.assignees)
        .filter(User.id == current_user.id)
        .order_by(Content.updated_at.desc())
        .limit(50)
        .all()
    )
    
    # 获取我负责的会议（所有社区）
    assigned_meetings = (
        db.query(Meeting)
        .join(Meeting.assignees)
        .filter(User.id == current_user.id)
        .order_by(Meeting.scheduled_at.desc())
        .limit(50)
        .all()
    )
    
    # 统计工作状态
    content_stats = _calculate_work_status_stats(assigned_contents)
    meeting_stats = _calculate_work_status_stats(assigned_meetings)
    
    # 格式化响应数据
    content_items = [
        AssignedItem(
            id=content.id,
            type="content",
            title=content.title,
            work_status=content.work_status,
            status=content.status,
            created_at=content.created_at,
            updated_at=content.updated_at,
            scheduled_at=content.scheduled_publish_at,
            assignee_count=len(content.assignees),
            creator_name=content.creator.username if content.creator else None,
        )
        for content in assigned_contents
    ]
    
    meeting_items = [
        AssignedItem(
            id=meeting.id,
            type="meeting",
            title=meeting.title,
            work_status=_map_meeting_status_to_work_status(meeting.status),
            status=meeting.status,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at,
            scheduled_at=meeting.scheduled_at,
            assignee_count=len(meeting.assignees),
            creator_name=meeting.created_by.username if meeting.created_by else None,
        )
        for meeting in assigned_meetings
    ]
    
    return DashboardResponse(
        contents=content_items,
        meetings=meeting_items,
        content_stats=content_stats,
        meeting_stats=meeting_stats,
        total_assigned_items=len(assigned_contents) + len(assigned_meetings),
    )


@router.get("/assigned/contents", response_model=List[AssignedItem])
async def get_assigned_contents(
    work_status: Optional[str] = Query(None, description="Filter by work_status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取我负责的所有内容（跨所有社区）"""
    query = (
        db.query(Content)
        .join(Content.assignees)
        .filter(User.id == current_user.id)
    )
    
    if work_status:
        query = query.filter(Content.work_status == work_status)
    
    contents = query.order_by(Content.updated_at.desc()).all()
    
    return [
        AssignedItem(
            id=content.id,
            type="content",
            title=content.title,
            work_status=content.work_status,
            status=content.status,
            created_at=content.created_at,
            updated_at=content.updated_at,
            scheduled_at=content.scheduled_publish_at,
            assignee_count=len(content.assignees),
            creator_name=content.creator.username if content.creator else None,
        )
        for content in contents
    ]


@router.get("/assigned/meetings", response_model=List[AssignedItem])
async def get_assigned_meetings(
    work_status: Optional[str] = Query(None, description="Filter by work_status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取我负责的所有会议（跨所有社区）"""
    query = (
        db.query(Meeting)
        .join(Meeting.assignees)
        .filter(User.id == current_user.id)
    )
    
    # Map work_status filter to meeting status
    if work_status:
        status_mapping = {
            'planning': 'scheduled',
            'in_progress': 'in_progress',
            'completed': 'completed'
        }
        meeting_status = status_mapping.get(work_status)
        if meeting_status:
            query = query.filter(Meeting.status == meeting_status)
    
    meetings = query.order_by(Meeting.scheduled_at.desc()).all()
    
    return [
        AssignedItem(
            id=meeting.id,
            type="meeting",
            title=meeting.title,
            work_status=_map_meeting_status_to_work_status(meeting.status),
            status=meeting.status,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at,
            scheduled_at=meeting.scheduled_at,
            assignee_count=len(meeting.assignees),
            creator_name=meeting.created_by.username if meeting.created_by else None,
        )
        for meeting in meetings
    ]


@router.patch("/contents/{content_id}/work-status")
async def update_content_work_status(
    content_id: int,
    request: UpdateWorkStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新内容的工作状态"""
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # 验证用户权限（责任人或创建者）
    is_assignee = any(assignee.id == current_user.id for assignee in content.assignees)
    is_creator = content.created_by_user_id == current_user.id
    
    if not (is_assignee or is_creator or current_user.is_superuser):
        raise HTTPException(status_code=403, detail="Not authorized to update this content")
    
    old_status = content.work_status
    content.work_status = request.work_status
    db.commit()
    db.refresh(content)
    
    return {
        "id": content.id,
        "work_status": content.work_status,
        "old_status": old_status,
        "updated_at": content.updated_at,
    }


@router.patch("/meetings/{meeting_id}/work-status")
async def update_meeting_work_status(
    meeting_id: int,
    request: UpdateWorkStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新会议的工作状态（映射到 meeting.status）"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # 验证用户权限
    is_assignee = any(assignee.id == current_user.id for assignee in meeting.assignees)
    is_creator = meeting.created_by_user_id == current_user.id
    
    if not (is_assignee or is_creator or current_user.is_superuser):
        raise HTTPException(status_code=403, detail="Not authorized to update this meeting")
    
    # Map work_status to meeting status
    status_mapping = {
        'planning': 'scheduled',
        'in_progress': 'in_progress',
        'completed': 'completed'
    }
    
    old_status = meeting.status
    new_status = status_mapping.get(request.work_status, 'scheduled')
    meeting.status = new_status
    db.commit()
    db.refresh(meeting)
    
    return {
        "id": meeting.id,
        "work_status": request.work_status,
        "status": meeting.status,
        "old_status": old_status,
        "updated_at": meeting.updated_at,
    }


def _calculate_work_status_stats(items) -> WorkStatusStats:
    """计算工作状态统计"""
    stats = {"planning": 0, "in_progress": 0, "completed": 0}
    
    for item in items:
        # For Meeting objects, map status to work_status
        if isinstance(item, Meeting):
            work_status = _map_meeting_status_to_work_status(item.status)
        else:
            work_status = getattr(item, "work_status", "planning")
        
        if work_status in stats:
            stats[work_status] += 1
    
    return WorkStatusStats(**stats)


def _map_meeting_status_to_work_status(status: str) -> str:
    """将会议 status 映射为 work_status"""
    mapping = {
        'scheduled': 'planning',
        'in_progress': 'in_progress',
        'completed': 'completed',
        'cancelled': 'completed'  # 已取消的会议也算作已完成
    }
    return mapping.get(status, 'planning')
