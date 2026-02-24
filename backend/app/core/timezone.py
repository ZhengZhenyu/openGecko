from datetime import datetime
from datetime import timezone as _tz
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    """返回当前 UTC 时间（带时区信息）。"""
    return datetime.now(_tz.utc)


def get_app_tz() -> ZoneInfo:
    """返回配置的应用时区对象。"""
    from app.config import settings

    return ZoneInfo(settings.APP_TIMEZONE)


def to_app_tz(dt: datetime) -> datetime:
    """将 datetime 转换为应用时区。用于服务端输出（邮件、ICS 等）。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_tz.utc)
    return dt.astimezone(get_app_tz())
