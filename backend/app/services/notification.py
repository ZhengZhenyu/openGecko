from __future__ import annotations

import smtplib
from html import escape

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.timezone import utc_now
from app.models.community import Community
from app.models.meeting import Meeting, MeetingParticipant, MeetingReminder
from app.models.notification import NotificationType
from app.models.user import User
from app.services.email import EmailAttachment, EmailMessage, get_sender_info, get_smtp_config, send_email
from app.services.ics import build_meeting_ics
from app.services.notify import create_notification

logger = get_logger(__name__)


def send_meeting_reminder(db: Session, reminder_id: int) -> MeetingReminder:
    reminder = db.query(MeetingReminder).filter(MeetingReminder.id == reminder_id).first()
    if not reminder:
        raise ValueError("Reminder not found")

    if reminder.status == "sent":
        return reminder

    meeting = db.query(Meeting).filter(Meeting.id == reminder.meeting_id).first()
    if not meeting:
        reminder.status = "failed"
        reminder.error_message = "Meeting not found"
        db.commit()
        return reminder

    community = db.query(Community).filter(Community.id == meeting.community_id).first()
    if not community:
        reminder.status = "failed"
        reminder.error_message = "Community not found"
        db.commit()
        return reminder

    participants = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting.id
    ).all()
    recipient_emails = [p.email for p in participants if p.email]

    if not recipient_emails:
        reminder.status = "failed"
        reminder.error_message = "No recipients"
        db.commit()
        return reminder

    smtp_config, email_cfg = get_smtp_config(community)
    if not smtp_config:
        reminder.status = "failed"
        reminder.error_message = "SMTP not configured"
        db.commit()
        return reminder

    from_email, from_name, reply_to = get_sender_info(community, email_cfg)

    subject = f"[{meeting.title}] Meeting reminder"
    text_body = _build_text_body(meeting, community)
    html_body = _build_html_body(meeting, community)
    ics_content = build_meeting_ics(meeting, community, organizer_email=from_email)

    message = EmailMessage(
        subject=subject,
        to_emails=recipient_emails,
        html_body=html_body,
        text_body=text_body,
        from_email=from_email,
        from_name=from_name,
        reply_to=reply_to,
        attachments=[
            EmailAttachment(
                filename="meeting.ics",
                content=ics_content,
                mime_type="text/calendar",
            )
        ],
    )

    try:
        send_email(community, message)
        reminder.status = "sent"
        reminder.sent_at = utc_now()
        reminder.error_message = None
    except smtplib.SMTPException as exc:
        reminder.status = "failed"
        reminder.error_message = f"SMTP error: {str(exc)}"
    except Exception as exc:
        reminder.status = "failed"
        reminder.error_message = f"Error: {str(exc)}"

    db.commit()

    # 站内通知：无论邮件是否成功，均为有账号的与会者创建站内提醒
    _create_in_app_reminders(db, meeting, recipient_emails)

    return reminder


def _create_in_app_reminders(db: Session, meeting: Meeting, recipient_emails: list[str]) -> None:
    """根据与会者邮件列表查找系统用户，并创建站内会议提醒通知。"""
    if not recipient_emails:
        return
    time_str = meeting.scheduled_at.strftime("%m-%d %H:%M")
    users = db.query(User).filter(User.email.in_(recipient_emails)).all()
    for user in users:
        try:
            create_notification(
                db,
                user_id=user.id,
                ntype=NotificationType.MEETING_REMINDER,
                title=f"会议即将开始：{meeting.title}",
                body=f"开始时间：{time_str}，时长 {meeting.duration} 分钟",
                resource_type="meeting",
                resource_id=meeting.id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("创建会议站内提醒失败", extra={"user_id": user.id, "error": str(exc)})


def _build_text_body(meeting: Meeting, community: Community) -> str:
    parts = [
        f"Community: {community.name}",
        f"Title: {meeting.title}",
        f"Time: {meeting.scheduled_at.strftime('%Y-%m-%d %H:%M')}",
        f"Duration: {meeting.duration} minutes",
    ]
    if meeting.location:
        parts.append(f"Location: {meeting.location}")
    if meeting.agenda:
        parts.append(f"Agenda:\n{meeting.agenda}")
    return "\n".join(parts)


def _build_html_body(meeting: Meeting, community: Community) -> str:
    title = escape(meeting.title)
    community_name = escape(community.name)
    location = escape(meeting.location or "")
    agenda = escape(meeting.agenda or "")
    time_str = meeting.scheduled_at.strftime("%Y-%m-%d %H:%M")

    return (
        "<html><body style=\"font-family: Arial, sans-serif; max-width: 640px; margin: 0 auto;\">"
        f"<h2>{title}</h2>"
        f"<p><strong>Community:</strong> {community_name}</p>"
        f"<p><strong>Time:</strong> {time_str}</p>"
        f"<p><strong>Duration:</strong> {meeting.duration} minutes</p>"
        f"<p><strong>Location:</strong> {location}</p>"
        f"<p><strong>Agenda:</strong></p>"
        f"<pre style=\"white-space: pre-wrap;\">{agenda}</pre>"
        "</body></html>"
    )
