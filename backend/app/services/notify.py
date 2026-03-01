"""通用通知工具 — 写入站内通知并（可选）发送邮件。

使用方式：
    from app.services.notify import create_notification
    from app.models.notification import NotificationType

    create_notification(
        db,
        user_id=42,
        ntype=NotificationType.TASK_ASSIGNED,
        title="你被指派了任务：发布年度报告",
        body="活动：2024 开源峰会",
        resource_type="event_task",
        resource_id=7,
    )
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import get_logger
from app.models.notification import Notification, NotificationType
from app.models.user import User

logger = get_logger(__name__)


def create_notification(
    db: Session,
    user_id: int,
    ntype: NotificationType,
    title: str,
    body: str | None = None,
    resource_type: str | None = None,
    resource_id: int | None = None,
) -> Notification:
    """创建站内通知并持久化到数据库。

    若全局 SMTP 已配置，同时异步尝试发送邮件；失败时仅记日志，不抛出异常。
    """
    notif = Notification(
        user_id=user_id,
        type=ntype.value,
        title=title,
        body=body,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    # 可选：发送邮件通知
    _try_send_email(db, notif)

    return notif


def _try_send_email(db: Session, notif: Notification) -> None:
    """尝试向通知接收者发送邮件。失败时仅记录日志。"""
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        return

    try:
        user = db.get(User, notif.user_id)
        if not user or not user.email:
            return

        from app.services.email import EmailMessage, SmtpConfig, SmtpEmailProvider

        smtp_cfg = SmtpConfig(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
        )
        provider = SmtpEmailProvider(smtp_cfg)

        text_body = notif.title
        if notif.body:
            text_body += f"\n\n{notif.body}"

        html_body = f"<p><strong>{notif.title}</strong></p>"
        if notif.body:
            html_body += f"<p>{notif.body}</p>"

        message = EmailMessage(
            subject=notif.title,
            to_emails=[user.email],
            html_body=html_body,
            text_body=text_body,
            from_email=settings.SMTP_FROM_EMAIL,
        )
        provider.send(message)
        logger.info("通知邮件已发送", extra={"user_id": notif.user_id, "notif_id": notif.id})
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "通知邮件发送失败（站内通知已创建）",
            extra={"user_id": notif.user_id, "notif_id": notif.id, "error": str(exc)},
        )
