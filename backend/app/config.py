import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Community Content Hub"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./content_hub.db"

    # File storage
    UPLOAD_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # WeChat Official Account
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""
    WECHAT_API_BASE: str = "https://api.weixin.qq.com"

    # Hugo blog
    HUGO_REPO_PATH: str = ""
    HUGO_CONTENT_DIR: str = "content/posts"

    # CSDN (reserved)
    CSDN_COOKIE: str = ""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
