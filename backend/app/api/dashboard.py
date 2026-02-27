"""
个人工作台 API - 用户视角的统一视图
"""
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, subqueryload

from app.core.dependencies import get_current_active_superuser, get_current_user, get_db
from app.models.content import Content, content_assignees
from app.models.event import ChecklistItem, Event, EventTask
from app.models.meeting import Meeting, meeting_assignees
from app.models.user import User
from app.schemas.dashboard import (
    AssignedChecklistItem,
    AssignedEventTask,
    AssignedItem,
    ContentByTypeStats,
    DashboardResponse,
    UpdateWorkStatusRequest,
    UserWorkloadItem,
    WorkloadOverviewResponse,
    WorkStatusStats,
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

    # 获取我负责的内容（所有社区）—— subqueryload 预加载 assignees ，避免后续 len() 触发悰性加载
    assigned_contents = (
        db.query(Content)
        .join(Content.assignees)
        .filter(User.id == current_user.id)
        .options(subqueryload(Content.assignees))
        .order_by(Content.updated_at.desc())
        .limit(50)
        .all()
    )

    # 获取我负责的会议（所有社区）—— subqueryload 预加载 assignees
    assigned_meetings = (
        db.query(Meeting)
        .join(Meeting.assignees)
        .filter(User.id == current_user.id)
        .options(subqueryload(Meeting.assignees))
        .order_by(Meeting.scheduled_at.desc())
        .limit(50)
        .all()
    )

    # 统计工作状态
    content_stats = _calculate_work_status_stats(assigned_contents)
    meeting_stats = _calculate_work_status_stats(assigned_meetings)

    # 获取我负责的活动任务（Python 层过滤 JSON 数组）
    all_event_tasks = (
        db.query(EventTask)
        .join(Event, EventTask.event_id == Event.id)
        .filter(EventTask.assignee_ids.isnot(None))
        .order_by(EventTask.end_date.asc().nullslast())
        .limit(200)
        .all()
    )
    # 过滤出包含当前用户 ID 的任务
    my_event_tasks = [
        t for t in all_event_tasks
        if current_user.id in (t.assignee_ids or [])
    ]
    # 预查询 event 标题
    event_ids = list({t.event_id for t in my_event_tasks})
    event_titles: dict[int, str] = {}
    if event_ids:
        events = db.query(Event).filter(Event.id.in_(event_ids)).all()
        event_titles = {e.id: e.title for e in events}

    event_task_items = [
        AssignedEventTask(
            id=t.id,
            title=t.title,
            task_type=t.task_type,
            phase=t.phase,
            status=t.status,
            start_date=t.start_date,
            end_date=t.end_date,
            progress=t.progress,
            event_id=t.event_id,
            event_title=event_titles.get(t.event_id),
        )
        for t in my_event_tasks
    ]

    # 获取我负责的活动清单项（Python 层过滤 JSON 数组）
    all_checklist_items = (
        db.query(ChecklistItem)
        .join(Event, ChecklistItem.event_id == Event.id)
        .filter(ChecklistItem.assignee_ids.isnot(None))
        .order_by(ChecklistItem.due_date.asc().nullslast())
        .limit(200)
        .all()
    )
    my_checklist_items = [
        c for c in all_checklist_items
        if current_user.id in (c.assignee_ids or [])
    ]
    # 预查询清单项所属的 event 标题（合并 event_ids）
    checklist_event_ids = list({c.event_id for c in my_checklist_items} - set(event_ids))
    if checklist_event_ids:
        extra_events = db.query(Event).filter(Event.id.in_(checklist_event_ids)).all()
        event_titles.update({e.id: e.title for e in extra_events})

    checklist_items_out = [
        AssignedChecklistItem(
            id=c.id,
            title=c.title,
            phase=c.phase,
            status=c.status,
            due_date=c.due_date,
            event_id=c.event_id,
            event_title=event_titles.get(c.event_id),
        )
        for c in my_checklist_items
    ]

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
        event_tasks=event_task_items,
        checklist_items=checklist_items_out,
        content_stats=content_stats,
        meeting_stats=meeting_stats,
        event_task_stats=_calculate_work_status_stats(my_event_tasks),
        checklist_item_stats=_calculate_work_status_stats(my_checklist_items),
        total_assigned_items=len(assigned_contents) + len(assigned_meetings) + len(my_event_tasks) + len(my_checklist_items),
    )


@router.get("/assigned/contents", response_model=list[AssignedItem])
async def get_assigned_contents(
    work_status: str | None = Query(None, description="Filter by work_status"),
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

    contents = (
        query.options(subqueryload(Content.assignees))
        .order_by(Content.updated_at.desc())
        .all()
    )

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


@router.get("/assigned/meetings", response_model=list[AssignedItem])
async def get_assigned_meetings(
    work_status: str | None = Query(None, description="Filter by work_status"),
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

    meetings = (
        query.options(subqueryload(Meeting.assignees))
        .order_by(Meeting.scheduled_at.desc())
        .all()
    )

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


@router.get("/workload-overview", response_model=WorkloadOverviewResponse)
async def get_workload_overview(
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    获取所有用户的工作量总览（仅超级管理员）
    统计每个用户的内容和会议数量，按状态和类别分组
    """
    # 获取所有非默认管理员用户
    users = (
        db.query(User)
        .filter(User.is_default_admin == False)  # noqa: E712
        .order_by(User.id)
        .all()
    )

    if not users:
        return WorkloadOverviewResponse(users=[])

    user_ids = [u.id for u in users]

    # 一次性加载所有用户的内容分配（下面 2 次 DB 查询替代 N×2 次）
    content_rows = (
        db.query(Content, content_assignees.c.user_id)
        .join(content_assignees, Content.id == content_assignees.c.content_id)
        .filter(content_assignees.c.user_id.in_(user_ids))
        .all()
    )
    user_contents: dict[int, list] = defaultdict(list)
    for content, uid in content_rows:
        user_contents[uid].append(content)

    # 一次性加载所有用户的会议分配
    meeting_rows = (
        db.query(Meeting, meeting_assignees.c.user_id)
        .join(meeting_assignees, Meeting.id == meeting_assignees.c.meeting_id)
        .filter(meeting_assignees.c.user_id.in_(user_ids))
        .all()
    )
    user_meetings: dict[int, list] = defaultdict(list)
    for meeting, uid in meeting_rows:
        user_meetings[uid].append(meeting)

    # 一次性加载所有活动任务（JSON 过滤在 Python 层做）
    all_event_tasks = (
        db.query(EventTask)
        .filter(EventTask.assignee_ids.isnot(None))
        .all()
    )
    user_event_tasks: dict[int, list] = defaultdict(list)
    for t in all_event_tasks:
        for uid in (t.assignee_ids or []):
            if uid in set(user_ids):
                user_event_tasks[uid].append(t)

    # 一次性加载所有清单项（JSON 过滤在 Python 层做）
    all_checklist_items_wl = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.assignee_ids.isnot(None))
        .all()
    )
    user_checklist_items: dict[int, list] = defaultdict(list)
    for c in all_checklist_items_wl:
        for uid in (c.assignee_ids or []):
            if uid in set(user_ids):
                user_checklist_items[uid].append(c)

    result = []
    for user in users:
        assigned_contents = user_contents.get(user.id, [])
        assigned_meetings = user_meetings.get(user.id, [])
        assigned_event_tasks = user_event_tasks.get(user.id, [])
        assigned_checklist = user_checklist_items.get(user.id, [])

        content_stats = _calculate_work_status_stats(assigned_contents)
        meeting_stats = _calculate_work_status_stats(assigned_meetings)
        event_task_stats = _calculate_work_status_stats(assigned_event_tasks)
        checklist_item_stats = _calculate_work_status_stats(assigned_checklist)

        type_stats = {"contribution": 0, "release_note": 0, "event_summary": 0}
        for content in assigned_contents:
            st = content.source_type or "contribution"
            if st in type_stats:
                type_stats[st] += 1

        event_tasks_count = len(assigned_event_tasks)
        checklist_count = len(assigned_checklist)

        result.append(UserWorkloadItem(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            content_stats=content_stats,
            meeting_stats=meeting_stats,
            event_task_stats=event_task_stats,
            checklist_item_stats=checklist_item_stats,
            content_by_type=ContentByTypeStats(**type_stats),
            total=len(assigned_contents) + len(assigned_meetings) + event_tasks_count + checklist_count,
        ))

    return WorkloadOverviewResponse(users=result)


def _calculate_work_status_stats(items) -> WorkStatusStats:
    """计算工作状态统计（含逾期：未完成且截止日已过）
    支持 Content / Meeting / EventTask / ChecklistItem 对象。
    """
    from datetime import date as date_type
    from datetime import datetime as datetime_type

    from app.core.timezone import utc_now
    now = utc_now()
    today = now.date()
    stats = {"planning": 0, "in_progress": 0, "completed": 0, "overdue": 0}

    for item in items:
        if isinstance(item, ChecklistItem):
            # pending → planning；done / skipped → completed
            status = item.status
            work_status = "completed" if status in ("done", "skipped") else "planning"
            deadline = item.due_date  # date | None
        elif isinstance(item, EventTask):
            _et_map = {
                "not_started": "planning",
                "in_progress": "in_progress",
                "completed": "completed",
                "blocked": "in_progress",
            }
            work_status = _et_map.get(item.status, "planning")
            deadline = item.end_date  # date | None
        elif isinstance(item, Meeting):
            work_status = _map_meeting_status_to_work_status(item.status)
            deadline = getattr(item, "scheduled_at", None)
        else:
            work_status = getattr(item, "work_status", "planning")
            deadline = getattr(item, "scheduled_publish_at", None)

        if work_status in stats:
            stats[work_status] += 1

        # 逾期：未完成 且 有截止日 且 已过截止日
        if work_status != "completed" and deadline is not None:
            if isinstance(deadline, date_type) and not isinstance(deadline, datetime_type):
                # date 对象（ChecklistItem.due_date / EventTask.end_date）
                if deadline < today:
                    stats["overdue"] += 1
            else:
                # datetime 对象（Content / Meeting）
                dl = deadline.replace(tzinfo=None) if deadline.tzinfo else deadline
                nw = now.replace(tzinfo=None) if now.tzinfo else now
                if dl < nw:
                    stats["overdue"] += 1

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
