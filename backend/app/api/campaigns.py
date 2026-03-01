import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_user
from app.core.timezone import utc_now
from app.database import get_db
from app.models import User
from app.models.campaign import Campaign, CampaignActivity, CampaignContact, CampaignTask
from app.models.committee import Committee, CommitteeMember
from app.models.event import Event, EventAttendee
from app.models.people import PersonProfile
from app.schemas.campaign import (
    ActivityCreate,
    ActivityOut,
    BulkImportFromCommittees,
    BulkImportFromEvent,
    BulkImportFromPeople,
    BulkStatusUpdate,
    CampaignCreate,
    CampaignFunnel,
    CampaignListOut,
    CampaignOut,
    CampaignTaskCreate,
    CampaignTaskOut,
    CampaignTaskUpdate,
    CampaignUpdate,
    CommitteeSimple,
    ContactCreate,
    ContactOut,
    ContactStatusUpdate,
    CsvImportResult,
    PaginatedContacts,
)

router = APIRouter()

VALID_TYPES = {
    "default", "community_care", "developer_care",  # 新版三类
    "promotion", "care", "invitation", "survey",   # 旧版兼容
}
VALID_STATUSES = {"active", "completed"}
VALID_CONTACT_STATUSES = {"pending", "contacted", "blocked"}


# ─── Campaign CRUD ─────────────────────────────────────────────────────────────

@router.get("", response_model=list[CampaignListOut])
def list_campaigns(
    type: str | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Campaign)
    if type:
        query = query.filter(Campaign.type == type)
    if status:
        query = query.filter(Campaign.status == status)
    return query.order_by(Campaign.created_at.desc()).all()


@router.post("", response_model=CampaignOut, status_code=201)
def create_campaign(
    data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.type not in VALID_TYPES:
        raise HTTPException(400, f"type 必须为 {VALID_TYPES}")
    dump = data.model_dump()
    # owner_ids 未指定时默认为当前登录用户
    if not dump.get("owner_ids"):
        dump["owner_ids"] = [current_user.id]
    campaign = Campaign(**dump)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("/{cid}", response_model=CampaignOut)
def get_campaign(
    cid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = db.query(Campaign).filter(
        Campaign.id == cid
    ).first()
    if not campaign:
        raise HTTPException(404, "运营活动不存在")
    return campaign


@router.patch("/{cid}", response_model=CampaignOut)
def update_campaign(
    cid: int,
    data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = db.query(Campaign).filter(
        Campaign.id == cid
    ).first()
    if not campaign:
        raise HTTPException(404, "运营活动不存在")
    update_data = data.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] not in VALID_STATUSES:
        raise HTTPException(400, f"status 必须为 {VALID_STATUSES}")
    for key, value in update_data.items():
        setattr(campaign, key, value)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.delete("/{cid}", status_code=204)
def delete_campaign(
    cid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除运营活动（含所有联系人、任务、活动记录，不可逆）"""
    campaign = db.query(Campaign).filter(Campaign.id == cid).first()
    if not campaign:
        raise HTTPException(404, "运营活动不存在")
    db.delete(campaign)
    db.commit()


# ─── Funnel Stats ──────────────────────────────────────────────────────────────

@router.get("/{cid}/funnel", response_model=CampaignFunnel)
def campaign_funnel(
    cid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = db.query(Campaign).filter(
        Campaign.id == cid
    ).first()
    if not campaign:
        raise HTTPException(404, "运营活动不存在")
    rows = (
        db.query(CampaignContact.status, func.count())
        .filter(CampaignContact.campaign_id == cid)
        .group_by(CampaignContact.status)
        .all()
    )
    counts = dict(rows)
    total = sum(counts.values())
    return CampaignFunnel(
        pending=counts.get("pending", 0),
        contacted=counts.get("contacted", 0),
        blocked=counts.get("blocked", 0),
        total=total,
    )


# ─── Contacts ─────────────────────────────────────────────────────────────────

@router.get("/{cid}/contacts", response_model=PaginatedContacts)
def list_contacts(
    cid: int,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = db.query(Campaign).filter(
        Campaign.id == cid
    ).first()
    if not campaign:
        raise HTTPException(404, "运营活动不存在")
    query = db.query(CampaignContact).filter(CampaignContact.campaign_id == cid)
    if status:
        query = query.filter(CampaignContact.status == status)
    total = query.count()
    items = query.options(joinedload(CampaignContact.person)).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedContacts(items=items, total=total, page=page, page_size=page_size)


@router.post("/{cid}/contacts", response_model=ContactOut, status_code=201)
def add_contact(
    cid: int,
    data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = db.query(Campaign).filter(
        Campaign.id == cid
    ).first()
    if not campaign:
        raise HTTPException(404, "运营活动不存在")
    # 检查是否已存在
    existing = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == cid,
        CampaignContact.person_id == data.person_id,
    ).first()
    if existing:
        raise HTTPException(400, "该联系人已在此运营活动中")
    contact = CampaignContact(
        campaign_id=cid,
        added_by="manual",
        **data.model_dump(),
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.patch("/{cid}/contacts/{contact_id}/status", response_model=ContactOut)
def update_contact_status(
    cid: int,
    contact_id: int,
    data: ContactStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.status not in VALID_CONTACT_STATUSES:
        raise HTTPException(400, f"status 必须为 {VALID_CONTACT_STATUSES}")
    contact = db.query(CampaignContact).filter(
        CampaignContact.id == contact_id,
        CampaignContact.campaign_id == cid,
    ).first()
    if not contact:
        raise HTTPException(404, "联系人记录不存在")
    _allowed = {"status", "channel", "notes", "assigned_to_id"}
    for key, value in data.model_dump(exclude_unset=True).items():
        if key in _allowed:
            setattr(contact, key, value)
    db.commit()
    db.refresh(contact)
    return contact


# ─── Bulk Import ──────────────────────────────────────────────────────────────

@router.post("/{cid}/contacts/import-event", status_code=200)
def import_from_event(
    cid: int,
    data: BulkImportFromEvent,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从活动签到名单批量导入联系人。"""
    campaign = db.query(Campaign).filter(
        Campaign.id == cid
    ).first()
    if not campaign:
        raise HTTPException(404, "运营活动不存在")
    # 校验活动存在
    event = db.query(Event).filter(
        Event.id == data.event_id,
    ).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    attendees = db.query(EventAttendee).filter(EventAttendee.event_id == data.event_id).all()
    created = skipped = 0
    for att in attendees:
        existing = db.query(CampaignContact).filter(
            CampaignContact.campaign_id == cid,
            CampaignContact.person_id == att.person_id,
        ).first()
        if existing:
            skipped += 1
            continue
        db.add(CampaignContact(
            campaign_id=cid,
            person_id=att.person_id,
            channel=data.channel,
            assigned_to_id=data.assigned_to_id,
            added_by="event_import",
        ))
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}


@router.post("/{cid}/contacts/import-people", status_code=200)
def import_from_people(
    cid: int,
    data: BulkImportFromPeople,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从人脉库批量导入指定 person_id 列表。"""
    campaign = db.query(Campaign).filter(
        Campaign.id == cid
    ).first()
    if not campaign:
        raise HTTPException(404, "运营活动不存在")
    # 校验所有 person_id 真实存在
    if data.person_ids:
        existing_ids = {
            row[0] for row in db.query(PersonProfile.id).filter(
                PersonProfile.id.in_(data.person_ids)
            ).all()
        }
        invalid_ids = set(data.person_ids) - existing_ids
        if invalid_ids:
            raise HTTPException(400, f"以下人脉档案不存在: {sorted(invalid_ids)}")
    created = skipped = 0
    for pid in data.person_ids:
        existing = db.query(CampaignContact).filter(
            CampaignContact.campaign_id == cid,
            CampaignContact.person_id == pid,
        ).first()
        if existing:
            skipped += 1
            continue
        db.add(CampaignContact(
            campaign_id=cid,
            person_id=pid,
            channel=data.channel,
            assigned_to_id=data.assigned_to_id,
            added_by="manual",
        ))
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}


# ─── Committee Import ─────────────────────────────────────────────────────────

@router.get("/{cid}/available-committees", response_model=list[CommitteeSimple])
def list_available_committees(
    cid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """列出该运营活动关联社区下的所有委员会（用于 community_care 类型导入选择）。"""
    campaign = db.query(Campaign).filter(Campaign.id == cid).first()
    if not campaign:
        raise HTTPException(404, "运营活动不存在")
    if not campaign.community_id:
        raise HTTPException(400, "该运营活动未关联社区，无法导入委员会成员")

    committees = (
        db.query(Committee)
        .filter(Committee.community_id == campaign.community_id, Committee.is_active.is_(True))
        .all()
    )
    result = []
    for c in committees:
        member_count = db.query(func.count(CommitteeMember.id)).filter(
            CommitteeMember.committee_id == c.id
        ).scalar() or 0
        result.append(CommitteeSimple(id=c.id, name=c.name, member_count=member_count))
    return result


@router.post("/{cid}/contacts/import-committee", status_code=200)
def import_from_committees(
    cid: int,
    data: BulkImportFromCommittees,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从一个或多个委员会批量导入成员，自动去重，无 PersonProfile 的成员会自动创建档案。"""
    campaign = db.query(Campaign).filter(Campaign.id == cid).first()
    if not campaign:
        raise HTTPException(404, "运营活动不存在")
    if not data.committee_ids:
        return {"created": 0, "skipped": 0}

    # 验证委员会属于关联社区
    for committee_id in data.committee_ids:
        committee = db.query(Committee).filter(
            Committee.id == committee_id,
            Committee.community_id == campaign.community_id,
        ).first()
        if not committee:
            raise HTTPException(400, f"委员会 {committee_id} 不属于该活动关联的社区")

    members = (
        db.query(CommitteeMember)
        .filter(CommitteeMember.committee_id.in_(data.committee_ids))
        .all()
    )

    created = skipped = 0
    seen_person_ids: set[int] = set()

    for member in members:
        # 确保有 PersonProfile
        if member.person_id:
            person_id = member.person_id
        else:
            # 尝试按邮箱匹配已有档案
            existing_person = None
            if member.email:
                existing_person = db.query(PersonProfile).filter(
                    PersonProfile.email == member.email
                ).first()
            if not existing_person:
                # 自动创建
                existing_person = PersonProfile(
                    display_name=member.name,
                    email=member.email or None,
                    phone=member.phone or None,
                    company=member.organization or None,
                    github_handle=member.github_id or None,
                    source="manual",
                    created_by_id=current_user.id,
                )
                db.add(existing_person)
                db.flush()
                # 回写 person_id 到委员
                member.person_id = existing_person.id
            person_id = existing_person.id

        # 跨委员会去重
        if person_id in seen_person_ids:
            skipped += 1
            continue
        seen_person_ids.add(person_id)

        # 检查此 person 是否已在 campaign contacts
        contact_exists = db.query(CampaignContact).filter(
            CampaignContact.campaign_id == cid,
            CampaignContact.person_id == person_id,
        ).first()
        if contact_exists:
            skipped += 1
            continue

        db.add(CampaignContact(
            campaign_id=cid,
            person_id=person_id,
            channel=data.channel,
            assigned_to_id=data.assigned_to_id,
            added_by="ecosystem_import",
        ))
        created += 1

    db.commit()
    return {"created": created, "skipped": skipped}


# ─── CSV/Excel Import ─────────────────────────────────────────────────────────

@router.post("/{cid}/contacts/import-csv", response_model=CsvImportResult)
async def import_from_csv(
    cid: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传 CSV 文件批量导入联系人。
    表头（首行）：display_name,email,phone,company,github_handle,notes（display_name 必填）。
    自动去重：email 相同的从已有 PersonProfile 中匹配；已在 campaign 中的则跳过。
    """
    campaign = db.query(Campaign).filter(Campaign.id == cid).first()
    if not campaign:
        raise HTTPException(404, "运营活动不存在")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")  # 支持 Excel 导出带 BOM 的 UTF-8
    except UnicodeDecodeError:
        try:
            text = content.decode("gbk")
        except UnicodeDecodeError as exc:
            raise HTTPException(400, "文件编码不支持，请使用 UTF-8 或 GBK 编码的 CSV") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "display_name" not in reader.fieldnames:
        raise HTTPException(400, "CSV 文件缺少必填列 display_name")

    result = CsvImportResult()
    rows = list(reader)
    if len(rows) > 5000:
        raise HTTPException(400, "单次导入最多 5000 行")

    for idx, row in enumerate(rows, start=2):
        name = (row.get("display_name") or "").strip()
        if not name:
            result.errors.append(f"第 {idx} 行：display_name 为空，已跳过")
            continue

        email = (row.get("email") or "").strip() or None

        # 查找或创建 PersonProfile
        person: PersonProfile | None = None
        if email:
            person = db.query(PersonProfile).filter(PersonProfile.email == email).first()

        if person:
            result.matched += 1
        else:
            person = PersonProfile(
                display_name=name,
                email=email,
                phone=(row.get("phone") or "").strip() or None,
                company=(row.get("company") or "").strip() or None,
                github_handle=(row.get("github_handle") or "").strip() or None,
                notes=(row.get("notes") or "").strip() or None,
                source="manual",
                created_by_id=current_user.id,
            )
            db.add(person)
            db.flush()
            result.created += 1

        # 检查是否已在 campaign
        exists = db.query(CampaignContact).filter(
            CampaignContact.campaign_id == cid,
            CampaignContact.person_id == person.id,
        ).first()
        if exists:
            result.skipped += 1
            continue

        db.add(CampaignContact(
            campaign_id=cid,
            person_id=person.id,
            added_by="csv_import",
        ))

    db.commit()
    return result


# ─── Bulk Status Update ──────────────────────────────────────────────────────

@router.patch("/{cid}/contacts/bulk-status")
def bulk_update_contact_status(
    cid: int,
    data: BulkStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量更新多个联系人状态"""
    if data.status not in VALID_CONTACT_STATUSES:
        raise HTTPException(400, f"status 必须为 {VALID_CONTACT_STATUSES}")
    campaign = db.query(Campaign).filter(Campaign.id == cid).first()
    if not campaign:
        raise HTTPException(404, "运营活动不存在")
    contacts = (
        db.query(CampaignContact)
        .filter(
            CampaignContact.id.in_(data.contact_ids),
            CampaignContact.campaign_id == cid,
        )
        .all()
    )
    for contact in contacts:
        contact.status = data.status
        if data.notes is not None:
            contact.notes = data.notes
    db.commit()
    return {"updated": len(contacts)}


# ─── Activities ───────────────────────────────────────────────────────────────

@router.get("/{cid}/contacts/{contact_id}/activities", response_model=list[ActivityOut])
def list_activities(
    cid: int,
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(CampaignContact).filter(
        CampaignContact.id == contact_id,
        CampaignContact.campaign_id == cid,
    ).first()
    if not contact:
        raise HTTPException(404, "联系人记录不存在")
    return (
        db.query(CampaignActivity)
        .filter(
            CampaignActivity.campaign_id == cid,
            CampaignActivity.person_id == contact.person_id,
        )
        .order_by(CampaignActivity.created_at.desc())
        .all()
    )


@router.post("/{cid}/contacts/{contact_id}/activities", response_model=ActivityOut, status_code=201)
def add_activity(
    cid: int,
    contact_id: int,
    data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(CampaignContact).filter(
        CampaignContact.id == contact_id,
        CampaignContact.campaign_id == cid,
    ).first()
    if not contact:
        raise HTTPException(404, "联系人记录不存在")
    activity = CampaignActivity(
        campaign_id=cid,
        person_id=contact.person_id,
        operator_id=current_user.id,
        **data.model_dump(),
    )
    db.add(activity)
    # 更新联系人最近跟进时间
    contact.last_contacted_at = utc_now()
    db.commit()
    db.refresh(activity)
    return activity


# ─── Campaign Task CRUD ───────────────────────────────────────────────────────────────

@router.get("/{cid}/tasks", response_model=list[CampaignTaskOut])
def list_campaign_tasks(
    cid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取运营活动的任务列表"""
    campaign = db.query(Campaign).filter(Campaign.id == cid).first()
    if not campaign:
        raise HTTPException(404, "活动不存在")
    tasks = (
        db.query(CampaignTask)
        .filter(CampaignTask.campaign_id == cid)
        .order_by(CampaignTask.created_at.asc())
        .all()
    )
    return tasks


@router.post("/{cid}/tasks", response_model=CampaignTaskOut, status_code=201)
def create_campaign_task(
    cid: int,
    data: CampaignTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建运营活动任务"""
    campaign = db.query(Campaign).filter(Campaign.id == cid).first()
    if not campaign:
        raise HTTPException(404, "活动不存在")
    task = CampaignTask(
        campaign_id=cid,
        created_by_id=current_user.id,
        **data.model_dump(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{cid}/tasks/{tid}", response_model=CampaignTaskOut)
def update_campaign_task(
    cid: int,
    tid: int,
    data: CampaignTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新运营活动任务"""
    task = db.query(CampaignTask).filter(
        CampaignTask.id == tid, CampaignTask.campaign_id == cid
    ).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{cid}/tasks/{tid}", status_code=204)
def delete_campaign_task(
    cid: int,
    tid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除运营活动任务"""
    task = db.query(CampaignTask).filter(
        CampaignTask.id == tid, CampaignTask.campaign_id == cid
    ).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    db.delete(task)
    db.commit()
