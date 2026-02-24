from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.timezone import utc_now
from app.models.community import Community
from app.models.meeting import Meeting


def _format_dt_utc(dt: datetime) -> str:
    """将 datetime 格式化为 iCalendar UTC 格式（以 Z 结尾）。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def build_meeting_ics(meeting: Meeting, community: Community, organizer_email: str) -> bytes:
    dt_start = meeting.scheduled_at
    dt_end = meeting.scheduled_at + timedelta(minutes=meeting.duration or 0)

    description_parts = []
    if meeting.description:
        description_parts.append(meeting.description)
    if meeting.agenda:
        description_parts.append(f"Agenda:\n{meeting.agenda}")
    if meeting.location:
        description_parts.append(f"Location: {meeting.location}")

    description = "\n\n".join(description_parts) if description_parts else "Meeting reminder"
    location = meeting.location or ""
    uid = f"meeting-{meeting.id}@{community.slug}"
    dtstamp = _format_dt_utc(utc_now())

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//openGecko//Meeting//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{_format_dt_utc(dt_start)}",
        f"DTEND:{_format_dt_utc(dt_end)}",
        f"SUMMARY:{meeting.title}",
        f"LOCATION:{location}",
        f"DESCRIPTION:{_escape_text(description)}",
        f"ORGANIZER:MAILTO:{organizer_email}",
        "STATUS:CONFIRMED",
        "END:VEVENT",
        "END:VCALENDAR",
    ]

    return "\r\n".join(lines).encode("utf-8")


def _escape_text(value: str) -> str:
    """Escape special characters for iCalendar text fields."""
    # Order matters: escape backslash first
    return (
        value.replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\n", "\\n")
        .replace("\r", "")
    )
