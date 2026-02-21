import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "openGecko"
    DEBUG: bool = False

    # CORS
    # 生产环境请通过环境变量设置允许的域名列表，多个域名用逗号分隔
    # 示例: CORS_ORIGINS=https://app.example.com,https://admin.example.com
    # 开发环境默认允许本地前端调试地址
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """将逗号分隔的 CORS_ORIGINS 字符串转换为列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Rate Limiting（速率限制）
    # 登录端点限制（防止暴力破解）
    RATE_LIMIT_LOGIN: str = "10/minute"
    # 默认 API 端点限制
    RATE_LIMIT_DEFAULT: str = "120/minute"

    # Database
    DATABASE_URL: str = "sqlite:///./opengecko.db"

    # Database Connection Pool (for PostgreSQL/MySQL)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    # Default admin account (seeded on first run)
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    DEFAULT_ADMIN_EMAIL: str = "admin@example.com"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production-please-use-a-strong-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Email / SMTP configuration for password recovery
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    # Frontend URL for password reset links
    FRONTEND_URL: str = "http://localhost:3000"

    # File storage
    UPLOAD_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "info"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
