
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_superuser, get_current_community
from app.core.security import encrypt_value
from app.database import get_db
from app.models import User
from app.models.channel import ChannelConfig
from app.schemas.publish import ChannelConfigCreate, ChannelConfigOut, ChannelConfigUpdate

router = APIRouter()

# 支持的渠道类型
SUPPORTED_CHANNELS = {"wechat", "hugo", "csdn", "zhihu"}

# 敏感字段关键字
SENSITIVE_FIELDS = {"app_secret", "cookie", "token", "secret", "password", "api_key"}


def _mask_sensitive_config(config: dict) -> dict:
    """将敏感字段值脱敏后返回。"""
    masked = {}
    for k, v in config.items():
        if any(sf in k.lower() for sf in SENSITIVE_FIELDS) and v:
            masked[k] = "••••••" + str(v)[-4:] if len(str(v)) > 4 else "••••"
        else:
            masked[k] = v
    return masked


def _config_to_out(cfg: ChannelConfig) -> ChannelConfigOut:
    masked_config = _mask_sensitive_config(cfg.config) if cfg.config else {}
    return ChannelConfigOut(
        id=cfg.id,
        channel=cfg.channel,
        config=masked_config,
        enabled=cfg.enabled,
    )


@router.get("", response_model=list[ChannelConfigOut])
def list_channels(
    community_id: int = Depends(get_current_community),
    db: Session = Depends(get_db),
):
    """列出当前社区已配置的渠道。"""
    configs = (
        db.query(ChannelConfig)
        .filter(ChannelConfig.community_id == community_id)
        .all()
    )
    return [_config_to_out(cfg) for cfg in configs]


@router.post("", response_model=ChannelConfigOut, status_code=status.HTTP_201_CREATED)
def create_channel(
    data: ChannelConfigCreate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """为社区创建渠道配置。仅平台超级管理员可操作（渠道凭证属于高敏感信息）。"""
    if data.channel not in SUPPORTED_CHANNELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的渠道类型。可选: {', '.join(sorted(SUPPORTED_CHANNELS))}",
        )

    existing = (
        db.query(ChannelConfig)
        .filter(
            ChannelConfig.community_id == community_id,
            ChannelConfig.channel == data.channel,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"渠道 '{data.channel}' 已存在",
        )

    # 对敏感字段加密
    config = {}
    for k, v in data.config.items():
        if any(sf in k.lower() for sf in SENSITIVE_FIELDS) and v:
            config[k] = encrypt_value(v)
        else:
            config[k] = v

    cfg = ChannelConfig(
        channel=data.channel,
        community_id=community_id,
        config=config,
        enabled=data.enabled,
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return _config_to_out(cfg)


@router.put("/{channel_id}", response_model=ChannelConfigOut)
def update_channel(
    channel_id: int,
    data: ChannelConfigUpdate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """更新渠道配置。仅平台超级管理员可操作。"""
    cfg = (
        db.query(ChannelConfig)
        .filter(
            ChannelConfig.id == channel_id,
            ChannelConfig.community_id == community_id,
        )
        .first()
    )
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="渠道配置不存在",
        )

    if data.config:
        existing_config = dict(cfg.config or {})
        for k, v in data.config.items():
            if any(sf in k.lower() for sf in SENSITIVE_FIELDS):
                if v and not v.startswith("••••"):
                    existing_config[k] = encrypt_value(v)
            else:
                existing_config[k] = v
        cfg.config = existing_config

    if data.enabled is not None:
        cfg.enabled = data.enabled

    db.commit()
    db.refresh(cfg)
    return _config_to_out(cfg)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_channel(
    channel_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """删除社区的渠道配置。仅平台超级管理员可操作。"""
    cfg = (
        db.query(ChannelConfig)
        .filter(
            ChannelConfig.id == channel_id,
            ChannelConfig.community_id == community_id,
        )
        .first()
    )
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="渠道配置不存在",
        )
    db.delete(cfg)
    db.commit()
