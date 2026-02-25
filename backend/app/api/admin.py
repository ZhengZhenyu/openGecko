"""管理员专用 API — 目前仅包含配置 Schema 查询端点。"""
from fastapi import APIRouter, Depends

from app.config import Settings, settings
from app.core.dependencies import get_current_active_superuser
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
