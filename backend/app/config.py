import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = Field(default="openGecko", description="应用名称")
    DEBUG: bool = Field(default=False, description="调试模式（生产环境必须设为 false）")

    # ── CORS ──────────────────────────────────────────────────────────
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="允许的跨域来源，多个地址用英文逗号分隔。"
                    "生产环境示例: https://app.example.com,https://admin.example.com",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """将逗号分隔的 CORS_ORIGINS 字符串转换为列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # ── Rate Limiting ──────────────────────────────────────────────────
    RATE_LIMIT_LOGIN: str = Field(
        default="10/minute",
        description="登录端点速率限制（防止暴力破解）。格式: <次数>/<单位>，单位可为 second/minute/hour",
    )
    RATE_LIMIT_DEFAULT: str = Field(
        default="120/minute",
        description="默认 API 端点速率限制",
    )

    # ── Database ───────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="sqlite:///./data/opengecko.db",
        description="数据库连接 URL。"
                    "开发: sqlite:///./data/opengecko.db；"
                    "生产推荐 PostgreSQL: postgresql://user:pass@host:5432/db",
    )
    DB_POOL_SIZE: int = Field(default=5, description="数据库连接池大小（PostgreSQL/MySQL 生效）")
    DB_MAX_OVERFLOW: int = Field(default=10, description="连接池最大溢出连接数")
    DB_POOL_TIMEOUT: int = Field(default=30, description="获取连接的超时秒数")
    DB_POOL_RECYCLE: int = Field(default=3600, description="连接回收时间（秒），防止数据库长连接断开")
    DB_ECHO: bool = Field(default=False, description="是否打印所有 SQL 语句（调试用，生产禁用）")

    # ── Default Admin ──────────────────────────────────────────────────
    DEFAULT_ADMIN_USERNAME: str = Field(default="admin", description="初始管理员用户名（首次启动时创建）")
    DEFAULT_ADMIN_PASSWORD: str = Field(
        default="admin123",
        description="初始管理员密码（⚠️ 生产环境首次启动后立即修改）",
    )
    DEFAULT_ADMIN_EMAIL: str = Field(default="admin@example.com", description="初始管理员邮箱")

    # ── JWT ────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production-please-use-a-strong-secret-key",
        description="JWT 签名密钥（⚠️ 生产环境必须替换，建议 `openssl rand -hex 32` 生成）",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT 签名算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 7,
        description="访问令牌有效期（分钟）。默认 7 天 = 10080 分钟",
    )

    # ── SMTP ───────────────────────────────────────────────────────────
    SMTP_HOST: str = Field(default="", description="SMTP 服务器地址（留空则禁用邮件功能）")
    SMTP_PORT: int = Field(default=587, description="SMTP 端口（587=STARTTLS，465=SSL）")
    SMTP_USER: str = Field(default="", description="SMTP 登录用户名")
    SMTP_PASSWORD: str = Field(default="", description="SMTP 登录密码")
    SMTP_FROM_EMAIL: str = Field(default="", description="发件人邮箱地址")
    SMTP_USE_TLS: bool = Field(default=True, description="是否使用 TLS/STARTTLS 加密连接")

    # ── Frontend ───────────────────────────────────────────────────────
    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        description="前端访问地址，用于生成密码重置链接邮件中的跳转 URL",
    )

    # ── File Storage ───────────────────────────────────────────────────
    UPLOAD_DIR: str = Field(
        default=str(Path(__file__).resolve().parent.parent / "uploads"),
        description="本地文件上传目录（仅 STORAGE_BACKEND=local 时使用）",
    )
    MAX_UPLOAD_SIZE: int = Field(
        default=50 * 1024 * 1024,
        description="单次上传文件大小上限（字节）。默认 50MB = 52428800",
    )
    STORAGE_BACKEND: str = Field(
        default="local",
        description="文件存储后端。"
                    "local：本地文件系统（开发默认）；"
                    "s3：S3 兼容对象存储（MinIO / AWS S3 / 华为 OBS 等，生产推荐）",
    )

    # ── S3 / MinIO ─────────────────────────────────────────────────────
    S3_ENDPOINT_URL: str = Field(
        default="http://minio:9000",
        description="S3 兼容存储的访问端点。"
                    "MinIO Docker 内网: http://minio:9000；"
                    "AWS S3: https://s3.amazonaws.com；"
                    "华为 OBS: https://obs.<region>.myhuaweicloud.com",
    )
    S3_ACCESS_KEY: str = Field(default="minioadmin", description="S3/MinIO Access Key（用户名）")
    S3_SECRET_KEY: str = Field(default="minioadmin", description="S3/MinIO Secret Key（密码）")
    S3_BUCKET: str = Field(default="opengecko", description="S3 Bucket 名称")
    S3_PUBLIC_URL: str = Field(
        default="http://minio:9000/opengecko",
        description="Bucket 的公开访问基础 URL（nginx 将 /uploads/ 代理到此地址）。"
                    "内网部署保持默认；对外暴露时改为公网域名",
    )

    # ── Timezone ───────────────────────────────────────────────────────
    APP_TIMEZONE: str = Field(
        default="Asia/Shanghai",
        description="服务端时区，影响 ICS 日历和邮件通知中的时间显示。"
                    "数据库始终以 UTC 存储，此配置仅控制输出本地化。"
                    "IANA 时区列表: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
    )

    # ── Feature Modules ────────────────────────────────────────────────
    ENABLE_INSIGHTS_MODULE: bool = Field(
        default=True,
        description="启用「洞察与人脉」模块（人脉管理 + 生态洞察）。"
                    "设为 false 则不加载相关 API 路由，前端自动隐藏对应菜单。",
    )

    # ── Server ─────────────────────────────────────────────────────────
    HOST: str = Field(default="0.0.0.0", description="服务监听地址")
    PORT: int = Field(default=8000, description="服务监听端口")
    LOG_LEVEL: str = Field(
        default="info",
        description="日志级别。可选: debug / info / warning / error / critical",
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
