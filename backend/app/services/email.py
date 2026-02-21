from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings
from app.models.community import Community


@dataclass
class EmailAttachment:
    filename: str
    content: bytes
    mime_type: str


@dataclass
class EmailMessage:
    subject: str
    to_emails: list[str]
    html_body: str
    text_body: str
    from_email: str
    from_name: str | None = None
    reply_to: str | None = None
    attachments: list[EmailAttachment] | None = None


@dataclass
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    use_tls: bool


class SmtpEmailProvider:
    def __init__(self, config: SmtpConfig) -> None:
        self._config = config

    def send(self, message: EmailMessage) -> None:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = message.subject
        msg["From"] = self._format_from(message.from_email, message.from_name)
        msg["To"] = ", ".join(message.to_emails)
        if message.reply_to:
            msg["Reply-To"] = message.reply_to

        alternative = MIMEMultipart("alternative")
        alternative.attach(MIMEText(message.text_body, "plain", "utf-8"))
        alternative.attach(MIMEText(message.html_body, "html", "utf-8"))
        msg.attach(alternative)

        for attachment in message.attachments or []:
            part = MIMEBase(*attachment.mime_type.split("/", 1))
            part.set_payload(attachment.content)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{attachment.filename}"')
            msg.attach(part)

        # Auto-detect encryption method based on port
        # Port 465: SMTP_SSL (direct SSL/TLS connection)
        # Port 587/others: SMTP with STARTTLS (upgrade after connect)
        use_ssl = self._config.port == 465
        # Use username if provided, otherwise use from_email as username
        username = self._config.username.strip() if self._config.username else message.from_email

        if use_ssl:
            # Use SMTP_SSL for port 465
            with smtplib.SMTP_SSL(self._config.host, self._config.port, timeout=30) as server:
                if username and self._config.password:
                    server.login(username, self._config.password)
                server.sendmail(message.from_email, message.to_emails, msg.as_string())
        else:
            # Use SMTP with STARTTLS for port 587 and others
            with smtplib.SMTP(self._config.host, self._config.port, timeout=30) as server:
                if self._config.use_tls:
                    server.starttls()
                if username and self._config.password:
                    server.login(username, self._config.password)
                server.sendmail(message.from_email, message.to_emails, msg.as_string())

    @staticmethod
    def _format_from(email: str, name: str | None) -> str:
        if name:
            return f"{name} <{email}>"
        return email


def _load_email_settings(community: Community) -> dict:
    settings_data = community.settings or {}
    email_cfg = settings_data.get("email") if isinstance(settings_data, dict) else None
    return email_cfg or {}


def _get_fallback_smtp_config() -> SmtpConfig | None:
    if not settings.SMTP_HOST:
        return None
    return SmtpConfig(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=settings.SMTP_USE_TLS,
    )


def get_smtp_config(community: Community) -> tuple[SmtpConfig | None, dict]:
    email_cfg = _load_email_settings(community)
    if email_cfg.get("enabled") is False:
        return None, email_cfg

    smtp_cfg = email_cfg.get("smtp") if isinstance(email_cfg, dict) else None
    if isinstance(smtp_cfg, dict) and smtp_cfg.get("host"):
        config = SmtpConfig(
            host=str(smtp_cfg.get("host")),
            port=int(smtp_cfg.get("port", 587)),
            username=str(smtp_cfg.get("username", "")),
            password=str(smtp_cfg.get("password", "")),
            use_tls=bool(smtp_cfg.get("use_tls", True)),
        )
        return config, email_cfg

    return _get_fallback_smtp_config(), email_cfg


def get_sender_info(community: Community, email_cfg: dict) -> tuple[str, str | None, str | None]:
    from_email = email_cfg.get("from_email") or settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    from_name = email_cfg.get("from_name") or community.name
    reply_to = email_cfg.get("reply_to")
    return from_email, from_name, reply_to


def send_email(community: Community, message: EmailMessage) -> None:
    smtp_config, _ = get_smtp_config(community)
    if not smtp_config:
        raise ValueError("SMTP 未配置或已禁用")

    provider = SmtpEmailProvider(smtp_config)
    provider.send(message)
