from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_user
from app.core.timezone import utc_now
from app.database import get_db
from app.models import User
from app.models.campaign import Campaign, CampaignActivity, CampaignContact
from app.models.event import Event, EventAttendee
from app.models.people import PersonProfile
from app.schemas.campaign import (
    ActivityCreate,
    ActivityOut,
    BulkImportFromEvent,
    BulkImportFromPeople,
    CampaignCreate,
    CampaignFunnel,
    CampaignListOut,
    CampaignOut,
    CampaignUpdate,
    ContactCreate,
    ContactOut,
    ContactStatusUpdate,
    PaginatedContacts,
)

router = APIRouter()

VALID_TYPES = {"promotion", "care", "invitation", "survey"}
VALID_STATUSES = {"draft", "active", "completed", "archived"}
VALID_CONTACT_STATUSES = {"pending", "contacted", "responded", "converted", "declined"}


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
    campaign = Campaign(
        owner_id=current_user.id,
        **data.model_dump(),
    )
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
        responded=counts.get("responded", 0),
        converted=counts.get("converted", 0),
        declined=counts.get("declined", 0),
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
