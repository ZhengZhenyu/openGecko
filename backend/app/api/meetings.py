import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_community_admin, get_current_community
from app.database import get_db
from app.models import User
from app.models.committee import Committee, CommitteeMember
from app.models.meeting import Meeting, MeetingParticipant, MeetingReminder
from app.schemas.governance import (
    MeetingCreate,
    MeetingDetail,
    MeetingOut,
    MeetingParticipantCreate,
    MeetingParticipantImportResult,
    MeetingParticipantOut,
    MeetingReminderCreate,
    MeetingReminderOut,
    MeetingUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[MeetingOut])
def list_meetings(
    community_id: int = Depends(get_current_community),
    committee_id: int | None = Query(None, description="按委员会ID筛选"),
    start_date: date | None = Query(None, description="开始日期（含）"),
    end_date: date | None = Query(None, description="结束日期（含）"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    列出社区的会议记录。

    支持按委员会、日期范围筛选。
    """
    query = db.query(Meeting).filter(Meeting.community_id == community_id)

    if committee_id:
        query = query.filter(Meeting.committee_id == committee_id)

    if start_date:
        query = query.filter(Meeting.scheduled_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query = query.filter(Meeting.scheduled_at <= datetime.combine(end_date, datetime.max.time()))

    query = query.order_by(Meeting.scheduled_at.desc())

    meetings = query.offset(skip).limit(limit).all()

    # Build response with assignee_ids for each meeting
    result = []
    for meeting in meetings:
        meeting_dict = {
            **{c.name: getattr(meeting, c.name) for c in meeting.__table__.columns},
            "assignee_ids": [a.id for a in meeting.assignees]
        }
        result.append(meeting_dict)

    return result


@router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting(
    data: MeetingCreate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """
    创建新的会议记录。

    仅社区管理员可操作。
    """
    # 验证委员会属于当前社区
    committee = db.query(Committee).filter(
        Committee.id == data.committee_id,
        Committee.community_id == community_id,
    ).first()

    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="委员会不存在或不属于当前社区",
        )

    meeting = Meeting(
        committee_id=data.committee_id,
        community_id=community_id,
        title=data.title,
        description=data.description,
        scheduled_at=data.scheduled_at,
        duration=data.duration,
        location_type=data.location_type,
        location=data.location,
        agenda=data.agenda,
        status="scheduled",
        work_status="planning",  # 固定默认值，不对外暴露
        reminder_before_hours=data.reminder_before_hours,
        created_by_user_id=current_user.id,
    )

    db.add(meeting)
    db.flush()  # Get meeting ID

    # Assign assignees (default to creator if empty)
    assignee_ids = data.assignee_ids if data.assignee_ids else [current_user.id]
    for user_id in assignee_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            meeting.assignees.append(user)

    db.commit()
    db.refresh(meeting)

    # Build response with assignee_ids
    meeting_dict = {
        **{c.name: getattr(meeting, c.name) for c in meeting.__table__.columns},
        "assignee_ids": [a.id for a in meeting.assignees]
    }
    return meeting_dict


@router.get("/{meeting_id}", response_model=MeetingDetail)
def get_meeting(
    meeting_id: int,
    community_id: int = Depends(get_current_community),
    db: Session = Depends(get_db),
):
    """获取会议详情，包含委员会信息。"""
    meeting = (
        db.query(Meeting)
        .options(joinedload(Meeting.committee))
        .filter(
            Meeting.id == meeting_id,
            Meeting.community_id == community_id,
        )
        .first()
    )

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会议不存在",
        )

    # 构造返回数据
    meeting_dict = {
        "id": meeting.id,
        "committee_id": meeting.committee_id,
        "community_id": meeting.community_id,
        "title": meeting.title,
        "description": meeting.description,
        "scheduled_at": meeting.scheduled_at,
        "duration": meeting.duration,
        "location_type": meeting.location_type,
        "location": meeting.location,
        "status": meeting.status,
        "work_status": meeting.work_status,
        "agenda": meeting.agenda,
        "minutes": meeting.minutes,
        "attachments": meeting.attachments or [],
        "reminder_sent": meeting.reminder_sent,
        "created_by_user_id": meeting.created_by_user_id,
        "created_at": meeting.created_at,
        "updated_at": meeting.updated_at,
        "committee_name": meeting.committee.name if meeting.committee else "",
        "assignee_ids": [a.id for a in meeting.assignees]
    }

    return meeting_dict


@router.put("/{meeting_id}", response_model=MeetingOut)
def update_meeting(
    meeting_id: int,
    data: MeetingUpdate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """
    更新会议信息。

    仅社区管理员可操作。
    """
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.community_id == community_id,
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会议不存在",
        )

    # 如果更新委员会ID，需验证
    if data.committee_id is not None and data.committee_id != meeting.committee_id:
        committee = db.query(Committee).filter(
            Committee.id == data.committee_id,
            Committee.community_id == community_id,
        ).first()

        if not committee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="委员会不存在或不属于当前社区",
            )

    # 更新字段
    update_data = data.model_dump(exclude_unset=True)

    # Handle assignees update
    if "assignee_ids" in update_data:
        assignee_ids = update_data.pop("assignee_ids")
        meeting.assignees.clear()
        for user_id in assignee_ids:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                meeting.assignees.append(user)

    for field, value in update_data.items():
        setattr(meeting, field, value)

    db.commit()
    db.refresh(meeting)

    # Build response with assignee_ids
    meeting_dict = {
        **{c.name: getattr(meeting, c.name) for c in meeting.__table__.columns},
        "assignee_ids": [a.id for a in meeting.assignees]
    }
    return meeting_dict


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """
    删除会议记录。

    仅社区管理员可操作。会同时删除关联的提醒记录。
    """
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.community_id == community_id,
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会议不存在",
        )

    db.delete(meeting)
    db.commit()

    return None


@router.post("/{meeting_id}/reminders", response_model=MeetingReminderOut, status_code=status.HTTP_201_CREATED)
def create_reminder(
    meeting_id: int,
    reminder_data: MeetingReminderCreate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """
    为会议创建提醒记录。

    实际的通知发送依赖角色4的通知服务（预留）。
    reminder_type: 'preparation', 'one_week', 'three_days', 'one_day', 'two_hours', 'immediate'
    """
    # 验证会议存在
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.community_id == community_id,
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会议不存在",
        )

    # 计算提醒时间
    from datetime import timedelta
    reminder_type = reminder_data.reminder_type
    hours_map = {
        'preparation': meeting.reminder_before_hours or 24,
        'one_week': 168,
        'three_days': 72,
        'one_day': 24,
        'two_hours': 2,
        'immediate': 0,  # 立即发送
    }

    if reminder_type not in hours_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的提醒类型 '{reminder_type}'。可选值: {', '.join(sorted(hours_map.keys()))}",
        )

    hours_before = hours_map.get(reminder_type, 24)

    # For immediate reminders, set scheduled_at to now
    if reminder_type == 'immediate':
        scheduled_at = datetime.now()
    else:
        scheduled_at = meeting.scheduled_at - timedelta(hours=hours_before)

    reminder = MeetingReminder(
        meeting_id=meeting_id,
        reminder_type=reminder_type,
        scheduled_at=scheduled_at,
        notification_channels=['email'],
        status="pending",
    )

    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    # If immediate, trigger sending right away
    if reminder_type == 'immediate':
        from app.services.notification import send_meeting_reminder
        try:
            send_meeting_reminder(db, reminder.id)
            db.refresh(reminder)
        except Exception as e:
            # Even if sending fails, we still return the reminder
            # The error will be recorded in the reminder status
            logger.warning("立即发送提醒失败，reminder_id=%s: %s", reminder.id, e)

    return reminder


@router.get("/{meeting_id}/reminders", response_model=list[MeetingReminderOut])
def list_reminders(
    meeting_id: int,
    community_id: int = Depends(get_current_community),
    db: Session = Depends(get_db),
):
    """列出会议的所有提醒记录。"""
    # 验证会议存在且属于当前社区
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.community_id == community_id,
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会议不存在",
        )

    reminders = (
        db.query(MeetingReminder)
        .filter(MeetingReminder.meeting_id == meeting_id)
        .order_by(MeetingReminder.scheduled_at)
        .all()
    )

    return reminders


@router.get("/{meeting_id}/participants", response_model=list[MeetingParticipantOut])
def list_participants(
    meeting_id: int,
    community_id: int = Depends(get_current_community),
    db: Session = Depends(get_db),
):
    """列出会议的与会人。"""
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.community_id == community_id,
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会议不存在",
        )

    participants = (
        db.query(MeetingParticipant)
        .filter(MeetingParticipant.meeting_id == meeting_id)
        .order_by(MeetingParticipant.created_at.asc())
        .all()
    )

    return participants


@router.post("/{meeting_id}/participants", response_model=MeetingParticipantOut, status_code=status.HTTP_201_CREATED)
def add_participant(
    meeting_id: int,
    data: MeetingParticipantCreate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """手动添加会议与会人。"""
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.community_id == community_id,
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会议不存在",
        )

    existing = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id,
        MeetingParticipant.email == data.email,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已在与会人列表中",
        )

    participant = MeetingParticipant(
        meeting_id=meeting_id,
        name=data.name,
        email=data.email,
        source="manual",
    )

    db.add(participant)
    db.commit()
    db.refresh(participant)

    return participant


@router.delete("/{meeting_id}/participants/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(
    meeting_id: int,
    participant_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """删除会议与会人。"""
    participant = (
        db.query(MeetingParticipant)
        .join(Meeting, MeetingParticipant.meeting_id == Meeting.id)
        .filter(
            MeetingParticipant.id == participant_id,
            MeetingParticipant.meeting_id == meeting_id,
            Meeting.community_id == community_id,
        )
        .first()
    )

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="与会人不存在",
        )

    db.delete(participant)
    db.commit()

    return None


@router.post("/{meeting_id}/participants/import", response_model=MeetingParticipantImportResult)
def import_participants(
    meeting_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """从委员会成员导入会议与会人。"""
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.community_id == community_id,
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会议不存在",
        )

    members = db.query(CommitteeMember).filter(
        CommitteeMember.committee_id == meeting.committee_id,
        CommitteeMember.is_active.is_(True),
        CommitteeMember.email.isnot(None),
        CommitteeMember.email != "",
    ).all()

    # Get existing participant emails to avoid duplicates
    existing_emails = {
        email for (email,) in db.query(MeetingParticipant.email)
        .filter(MeetingParticipant.meeting_id == meeting_id)
        .all()
    }

    imported = 0
    skipped = 0
    participants = []

    for member in members:
        if member.email in existing_emails:
            skipped += 1
            continue

        participant = MeetingParticipant(
            meeting_id=meeting_id,
            name=member.name,
            email=member.email,
            source="committee_import",
        )
        db.add(participant)
        participants.append(participant)
        existing_emails.add(member.email)  # Prevent duplicates within this batch
        imported += 1

    if participants:
        db.commit()
        for participant in participants:
            db.refresh(participant)

    return MeetingParticipantImportResult(
        imported=imported,
        skipped=skipped,
        participants=participants,
    )


@router.get("/{meeting_id}/minutes")
def get_meeting_minutes(
    meeting_id: int,
    community_id: int = Depends(get_current_community),
    db: Session = Depends(get_db),
):
    """
    获取会议纪要。

    从会议的 minutes 字段返回纯文本或结构化内容。
    """
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.community_id == community_id,
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会议不存在",
        )

    return {
        "meeting_id": meeting.id,
        "title": meeting.title,
        "scheduled_at": meeting.scheduled_at,
        "minutes": meeting.minutes or "",
    }


@router.put("/{meeting_id}/minutes")
def update_meeting_minutes(
    meeting_id: int,
    minutes_data: dict,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """
    更新会议纪要。

    仅社区管理员可操作。接受 {"minutes": "纪要内容"} 格式。
    """
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.community_id == community_id,
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会议不存在",
        )

    if "minutes" not in minutes_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请求体必须包含 'minutes' 字段",
        )

    meeting.minutes = minutes_data["minutes"]
    db.commit()
    db.refresh(meeting)

    return {
        "meeting_id": meeting.id,
        "title": meeting.title,
        "minutes": meeting.minutes,
    }
