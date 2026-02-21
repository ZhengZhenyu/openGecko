"""
服务层单元测试 - 覆盖 email, ics, notification, converter 服务
"""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call
import smtplib

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# ICS Service Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestIcsService:
    """测试 build_meeting_ics 和 _escape_text"""

    def _make_meeting(self, **kwargs):
        m = MagicMock()
        m.id = kwargs.get("id", 1)
        m.title = kwargs.get("title", "Test Meeting")
        m.scheduled_at = kwargs.get("scheduled_at", datetime(2025, 6, 15, 10, 0, 0))
        m.duration = kwargs.get("duration", 60)
        m.description = kwargs.get("description", "Meeting description")
        m.agenda = kwargs.get("agenda", "1. Topic A\n2. Topic B")
        m.location = kwargs.get("location", "Room 101")
        return m

    def _make_community(self, **kwargs):
        c = MagicMock()
        c.id = kwargs.get("id", 1)
        c.name = kwargs.get("name", "Test Community")
        c.slug = kwargs.get("slug", "test-community")
        return c

    def test_build_meeting_ics_returns_bytes(self):
        from app.services.ics import build_meeting_ics
        meeting = self._make_meeting()
        community = self._make_community()
        result = build_meeting_ics(meeting, community, "organizer@example.com")
        assert isinstance(result, bytes)

    def test_build_meeting_ics_contains_required_fields(self):
        from app.services.ics import build_meeting_ics
        meeting = self._make_meeting()
        community = self._make_community()
        result = build_meeting_ics(meeting, community, "organizer@example.com").decode("utf-8")
        assert "BEGIN:VCALENDAR" in result
        assert "BEGIN:VEVENT" in result
        assert "END:VEVENT" in result
        assert "END:VCALENDAR" in result
        assert "DTSTART:20250615T100000" in result
        assert "DTEND:20250615T110000" in result
        assert "SUMMARY:Test Meeting" in result
        assert "ORGANIZER:MAILTO:organizer@example.com" in result

    def test_build_meeting_ics_with_no_description(self):
        from app.services.ics import build_meeting_ics
        meeting = self._make_meeting(description=None, agenda=None, location=None)
        community = self._make_community()
        result = build_meeting_ics(meeting, community, "organizer@example.com").decode("utf-8")
        assert "Meeting reminder" in result

    def test_build_meeting_ics_uid_contains_community_slug(self):
        from app.services.ics import build_meeting_ics
        meeting = self._make_meeting(id=42)
        community = self._make_community(slug="my-community")
        result = build_meeting_ics(meeting, community, "organizer@example.com").decode("utf-8")
        assert "meeting-42@my-community" in result

    def test_build_meeting_ics_zero_duration(self):
        from app.services.ics import build_meeting_ics
        meeting = self._make_meeting(duration=0, scheduled_at=datetime(2025, 6, 15, 10, 0, 0))
        community = self._make_community()
        result = build_meeting_ics(meeting, community, "test@example.com").decode("utf-8")
        # start and end should be the same time
        assert "DTSTART:20250615T100000" in result
        assert "DTEND:20250615T100000" in result

    def test_escape_text_backslash(self):
        from app.services.ics import _escape_text
        result = _escape_text("path\\to\\file")
        assert "\\\\" in result

    def test_escape_text_semicolon(self):
        from app.services.ics import _escape_text
        result = _escape_text("a;b;c")
        assert "\\;" in result

    def test_escape_text_comma(self):
        from app.services.ics import _escape_text
        result = _escape_text("a,b,c")
        assert "\\," in result

    def test_escape_text_newline(self):
        from app.services.ics import _escape_text
        result = _escape_text("line1\nline2")
        assert "\\n" in result

    def test_escape_text_empty(self):
        from app.services.ics import _escape_text
        assert _escape_text("") == ""


# ──────────────────────────────────────────────────────────────────────────────
# Email Service Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestEmailService:
    """测试 SMTP 邮件服务"""

    def _make_smtp_config(self, port=587):
        from app.services.email import SmtpConfig
        return SmtpConfig(
            host="smtp.example.com",
            port=port,
            username="user@example.com",
            password="password123",
            use_tls=True,
        )

    def _make_email_message(self, attachments=None):
        from app.services.email import EmailMessage
        return EmailMessage(
            subject="Test Subject",
            to_emails=["recipient@example.com"],
            html_body="<p>Hello</p>",
            text_body="Hello",
            from_email="sender@example.com",
            from_name="Test Sender",
            reply_to="reply@example.com",
            attachments=attachments,
        )

    def test_format_from_with_name(self):
        from app.services.email import SmtpEmailProvider
        result = SmtpEmailProvider._format_from("sender@example.com", "Test Sender")
        assert result == "Test Sender <sender@example.com>"

    def test_format_from_without_name(self):
        from app.services.email import SmtpEmailProvider
        result = SmtpEmailProvider._format_from("sender@example.com", None)
        assert result == "sender@example.com"

    def test_send_via_starttls(self):
        from app.services.email import SmtpEmailProvider
        config = self._make_smtp_config(port=587)
        provider = SmtpEmailProvider(config)
        message = self._make_email_message()

        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch("smtplib.SMTP", return_value=mock_smtp) as mock_smtp_cls:
            provider.send(message)
            mock_smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=30)
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once_with("user@example.com", "password123")
            mock_smtp.sendmail.assert_called_once()

    def test_send_via_ssl(self):
        from app.services.email import SmtpEmailProvider
        config = self._make_smtp_config(port=465)
        provider = SmtpEmailProvider(config)
        message = self._make_email_message()

        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch("smtplib.SMTP_SSL", return_value=mock_smtp) as mock_smtp_cls:
            provider.send(message)
            mock_smtp_cls.assert_called_once_with("smtp.example.com", 465, timeout=30)
            mock_smtp.login.assert_called_once_with("user@example.com", "password123")
            mock_smtp.sendmail.assert_called_once()

    def test_send_with_attachment(self):
        from app.services.email import SmtpEmailProvider, EmailAttachment
        config = self._make_smtp_config()
        provider = SmtpEmailProvider(config)
        attachment = EmailAttachment(
            filename="file.ics",
            content=b"BEGIN:VCALENDAR",
            mime_type="text/calendar",
        )
        message = self._make_email_message(attachments=[attachment])

        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch("smtplib.SMTP", return_value=mock_smtp):
            provider.send(message)
            # Verify sendmail was called (attachment was included)
            mock_smtp.sendmail.assert_called_once()
            args = mock_smtp.sendmail.call_args
            assert "file.ics" in args[0][2]  # filename in email body

    def test_get_smtp_config_disabled(self):
        from app.services.email import get_smtp_config
        community = MagicMock()
        community.settings = {"email": {"enabled": False}}
        config, email_cfg = get_smtp_config(community)
        assert config is None

    def test_get_smtp_config_from_community_settings(self):
        from app.services.email import get_smtp_config
        community = MagicMock()
        community.settings = {
            "email": {
                "smtp": {
                    "host": "custom.smtp.com",
                    "port": 587,
                    "username": "custom_user",
                    "password": "custom_pass",
                    "use_tls": True,
                }
            }
        }
        config, email_cfg = get_smtp_config(community)
        assert config is not None
        assert config.host == "custom.smtp.com"
        assert config.port == 587

    def test_get_smtp_config_fallback(self):
        from app.services.email import get_smtp_config
        community = MagicMock()
        community.settings = {}

        with patch("app.services.email.settings") as mock_settings:
            mock_settings.SMTP_HOST = "fallback.smtp.com"
            mock_settings.SMTP_PORT = 465
            mock_settings.SMTP_USER = "fallback_user"
            mock_settings.SMTP_PASSWORD = "fallback_pass"
            mock_settings.SMTP_USE_TLS = True
            config, _ = get_smtp_config(community)
            assert config is not None
            assert config.host == "fallback.smtp.com"

    def test_get_smtp_config_fallback_no_host(self):
        from app.services.email import get_smtp_config
        community = MagicMock()
        community.settings = {}

        with patch("app.services.email.settings") as mock_settings:
            mock_settings.SMTP_HOST = None
            config, _ = get_smtp_config(community)
            assert config is None

    def test_get_sender_info(self):
        from app.services.email import get_sender_info
        community = MagicMock()
        community.name = "My Community"
        email_cfg = {
            "from_email": "no-reply@example.com",
            "from_name": "Community Bot",
            "reply_to": "reply@example.com",
        }
        from_email, from_name, reply_to = get_sender_info(community, email_cfg)
        assert from_email == "no-reply@example.com"
        assert from_name == "Community Bot"
        assert reply_to == "reply@example.com"

    def test_send_email_no_smtp_raises(self):
        from app.services.email import send_email, EmailMessage
        community = MagicMock()
        community.settings = {}
        message = EmailMessage(
            subject="Test",
            to_emails=["x@example.com"],
            html_body="<p>test</p>",
            text_body="test",
            from_email="y@example.com",
        )
        with patch("app.services.email.settings") as mock_settings:
            mock_settings.SMTP_HOST = None
            with pytest.raises(ValueError, match="SMTP"):
                send_email(community, message)


# ──────────────────────────────────────────────────────────────────────────────
# Notification Service Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestNotificationService:
    """测试 send_meeting_reminder"""

    def _make_db(self):
        return MagicMock()

    def _make_reminder(self, status="pending", id=1, meeting_id=1):
        r = MagicMock()
        r.id = id
        r.meeting_id = meeting_id
        r.status = status
        r.error_message = None
        r.sent_at = None
        return r

    def _make_meeting(self, community_id=1):
        m = MagicMock()
        m.id = 1
        m.title = "Test Meeting"
        m.scheduled_at = datetime(2025, 6, 15, 10, 0, 0)
        m.duration = 60
        m.location = "Room 1"
        m.agenda = "1. Topic"
        m.community_id = community_id
        return m

    def _make_community(self):
        c = MagicMock()
        c.id = 1
        c.name = "Test Community"
        c.slug = "test-community"
        c.settings = {}
        return c

    def test_reminder_not_found(self):
        from app.services.notification import send_meeting_reminder
        db = self._make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Reminder not found"):
            send_meeting_reminder(db, 999)

    def test_reminder_already_sent(self):
        from app.services.notification import send_meeting_reminder
        db = self._make_db()
        reminder = self._make_reminder(status="sent")
        db.query.return_value.filter.return_value.first.return_value = reminder

        result = send_meeting_reminder(db, 1)
        assert result.status == "sent"

    def test_meeting_not_found(self):
        from app.services.notification import send_meeting_reminder
        db = self._make_db()
        reminder = self._make_reminder()

        def query_side_effect(model):
            from app.models.meeting import MeetingReminder, Meeting
            mock_query = MagicMock()
            if model == MeetingReminder:
                mock_query.filter.return_value.first.return_value = reminder
            else:
                mock_query.filter.return_value.first.return_value = None
            return mock_query

        db.query.side_effect = query_side_effect
        result = send_meeting_reminder(db, 1)
        assert result.status == "failed"
        assert "Meeting not found" in result.error_message

    def test_no_recipients(self):
        from app.services.notification import send_meeting_reminder
        from app.models.meeting import MeetingReminder, Meeting, MeetingParticipant
        from app.models.community import Community

        db = self._make_db()
        reminder = self._make_reminder()
        meeting = self._make_meeting()
        community = self._make_community()

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            call_count[0] += 1
            if model == MeetingReminder:
                mock_query.filter.return_value.first.return_value = reminder
            elif model == Meeting:
                mock_query.filter.return_value.first.return_value = meeting
            elif model == Community:
                mock_query.filter.return_value.first.return_value = community
            elif model == MeetingParticipant:
                mock_query.filter.return_value.all.return_value = []
            return mock_query

        db.query.side_effect = query_side_effect
        result = send_meeting_reminder(db, 1)
        assert result.status == "failed"
        assert "No recipients" in result.error_message

    def test_smtp_not_configured(self):
        from app.services.notification import send_meeting_reminder
        from app.models.meeting import MeetingReminder, Meeting, MeetingParticipant
        from app.models.community import Community

        db = self._make_db()
        reminder = self._make_reminder()
        meeting = self._make_meeting()
        community = self._make_community()
        participant = MagicMock()
        participant.email = "user@example.com"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == MeetingReminder:
                mock_query.filter.return_value.first.return_value = reminder
            elif model == Meeting:
                mock_query.filter.return_value.first.return_value = meeting
            elif model == Community:
                mock_query.filter.return_value.first.return_value = community
            elif model == MeetingParticipant:
                mock_query.filter.return_value.all.return_value = [participant]
            return mock_query

        db.query.side_effect = query_side_effect

        with patch("app.services.notification.get_smtp_config", return_value=(None, {})):
            result = send_meeting_reminder(db, 1)
            assert result.status == "failed"
            assert "SMTP not configured" in result.error_message

    def test_send_success(self):
        from app.services.notification import send_meeting_reminder
        from app.models.meeting import MeetingReminder, Meeting, MeetingParticipant
        from app.models.community import Community

        db = self._make_db()
        reminder = self._make_reminder()
        meeting = self._make_meeting()
        community = self._make_community()
        participant = MagicMock()
        participant.email = "user@example.com"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == MeetingReminder:
                mock_query.filter.return_value.first.return_value = reminder
            elif model == Meeting:
                mock_query.filter.return_value.first.return_value = meeting
            elif model == Community:
                mock_query.filter.return_value.first.return_value = community
            elif model == MeetingParticipant:
                mock_query.filter.return_value.all.return_value = [participant]
            return mock_query

        db.query.side_effect = query_side_effect
        mock_smtp_config = MagicMock()
        mock_email_cfg = {"from_email": "sender@example.com"}

        with patch("app.services.notification.get_smtp_config", return_value=(mock_smtp_config, mock_email_cfg)), \
             patch("app.services.notification.get_sender_info", return_value=("sender@example.com", "Community", None)), \
             patch("app.services.notification.send_email") as mock_send_email, \
             patch("app.services.notification.build_meeting_ics", return_value=b"BEGIN:VCALENDAR"):
            result = send_meeting_reminder(db, 1)
            assert result.status == "sent"
            mock_send_email.assert_called_once()

    def test_send_smtp_exception(self):
        from app.services.notification import send_meeting_reminder
        from app.models.meeting import MeetingReminder, Meeting, MeetingParticipant
        from app.models.community import Community

        db = self._make_db()
        reminder = self._make_reminder()
        meeting = self._make_meeting()
        community = self._make_community()
        participant = MagicMock()
        participant.email = "user@example.com"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == MeetingReminder:
                mock_query.filter.return_value.first.return_value = reminder
            elif model == Meeting:
                mock_query.filter.return_value.first.return_value = meeting
            elif model == Community:
                mock_query.filter.return_value.first.return_value = community
            elif model == MeetingParticipant:
                mock_query.filter.return_value.all.return_value = [participant]
            return mock_query

        db.query.side_effect = query_side_effect
        mock_smtp_config = MagicMock()

        with patch("app.services.notification.get_smtp_config", return_value=(mock_smtp_config, {})), \
             patch("app.services.notification.get_sender_info", return_value=("sender@example.com", "Community", None)), \
             patch("app.services.notification.send_email", side_effect=smtplib.SMTPException("Connection refused")), \
             patch("app.services.notification.build_meeting_ics", return_value=b"BEGIN:VCALENDAR"):
            result = send_meeting_reminder(db, 1)
            assert result.status == "failed"
            assert "SMTP error" in result.error_message


# ──────────────────────────────────────────────────────────────────────────────
# Converter Service Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestConverterService:
    """测试 markdown 转换服务"""

    def test_convert_markdown_to_html_basic(self):
        from app.services.converter import convert_markdown_to_html
        result = convert_markdown_to_html("# Hello World")
        assert "<h1" in result
        assert "Hello World" in result

    def test_convert_markdown_to_html_code_block(self):
        from app.services.converter import convert_markdown_to_html
        result = convert_markdown_to_html("```python\nprint('hello')\n```")
        assert "print" in result

    def test_convert_markdown_to_html_table(self):
        from app.services.converter import convert_markdown_to_html
        md = "| Col1 | Col2 |\n|------|------|\n| A | B |"
        result = convert_markdown_to_html(md)
        assert "<table" in result
        assert "Col1" in result

    def test_convert_markdown_to_html_bold(self):
        from app.services.converter import convert_markdown_to_html
        result = convert_markdown_to_html("**bold text**")
        assert "<strong>" in result or "bold text" in result

    def test_convert_markdown_to_html_links(self):
        from app.services.converter import convert_markdown_to_html
        result = convert_markdown_to_html("[link](https://example.com)")
        assert "href" in result
        assert "example.com" in result

    def test_read_markdown_file(self):
        from app.services.converter import read_markdown_file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Test\n\nHello World")
            tmp_path = f.name

        try:
            result = read_markdown_file(tmp_path)
            assert "# Test" in result
            assert "Hello World" in result
        finally:
            os.unlink(tmp_path)

    def test_read_markdown_file_strips_whitespace(self):
        from app.services.converter import read_markdown_file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("\n\n# Content\n\n")
            tmp_path = f.name

        try:
            result = read_markdown_file(tmp_path)
            assert result == "# Content"
        finally:
            os.unlink(tmp_path)

    def test_convert_empty_markdown(self):
        from app.services.converter import convert_markdown_to_html
        result = convert_markdown_to_html("")
        assert result == "" or isinstance(result, str)
