"""管理员专用 API — 配置 Schema 查询 + 审计日志查询。"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import Settings, settings
from app.core.dependencies import get_current_active_superuser, get_current_admin_or_superuser
from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import User

router = APIRouter()

# 包含敏感信息的字段名集合（值显示为 "***" 而不是真实内容）
_SENSITIVE_FIELDS = {
    "JWT_SECRET_KEY",
    "DEFAULT_ADMIN_PASSWORD",
    "SMTP_PASSWORD",
    "S3_SECRET_KEY",
}


@router.get("/config-schema")
def get_config_schema(
    current_user: User = Depends(get_current_active_superuser),
):
    """返回所有配置项的 JSON Schema（字段名、类型、描述、默认值）以及当前生效值。

    - 敏感字段（密钥、密码）的当前值以 `***` 脱敏显示
    - 仅超级管理员可访问
    """
    schema = Settings.model_json_schema()

    # 收集当前生效的配置值（脱敏处理）
    current_values: dict = {}
    for field_name in Settings.model_fields:
        raw = getattr(settings, field_name)
        if field_name.upper() in _SENSITIVE_FIELDS:
            current_values[field_name] = "***"
        else:
            current_values[field_name] = raw

    return {
        "schema": schema,
        "current_values": current_values,
    }


# ─── 审计日志 ───────────────────────────────────────────────────────────────────

@router.get("/audit-logs")
def list_audit_logs(
    action: str | None = Query(None, description="操作类型过滤，如 create_content"),
    resource_type: str | None = Query(None, description="资源类型过滤，如 content"),
    community_id: int | None = Query(None, description="社区 ID 过滤"),
    username: str | None = Query(None, description="用户名模糊过滤"),
    from_date: datetime | None = Query(None, description="开始时间（ISO 8601）"),
    to_date: datetime | None = Query(None, description="结束时间（ISO 8601）"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    current_user: User = Depends(get_current_admin_or_superuser),
    db: Session = Depends(get_db),
):
    """分页查询审计日志，需要管理员或超级管理员权限。"""
    query = (
        db.query(AuditLog, User.username, User.full_name)
        .join(User, AuditLog.user_id == User.id)
    )
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if community_id is not None:
        query = query.filter(AuditLog.community_id == community_id)
    if username:
        query = query.filter(User.username.ilike(f"%{username}%"))
    if from_date:
        query = query.filter(AuditLog.created_at >= from_date)
    if to_date:
        query = query.filter(AuditLog.created_at <= to_date)

    total = query.count()
    rows = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        {
            "id": log.id,
            "username": uname,
            "full_name": fname or uname,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "community_id": log.community_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log, uname, fname in rows
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}
