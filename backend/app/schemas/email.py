from pydantic import BaseModel, Field
from typing import Optional


class EmailSmtpConfig(BaseModel):
    host: str = Field(..., min_length=1, max_length=200, description="SMTP server hostname")
    port: int = Field(465, ge=1, le=65535, description="SMTP port: 465 for SSL/TLS, 587 for STARTTLS")
    username: str = Field("", max_length=200, description="Username (usually the email address, leave empty to use from_email)")
    password: str = Field("", max_length=200, description="SMTP password")
    use_tls: bool = Field(True, description="Use STARTTLS for port 587 (port 465 uses SSL by default)")


class EmailSettings(BaseModel):
    enabled: bool = True
    provider: str = "smtp"
    from_email: str = Field(..., min_length=1, max_length=200)
    from_name: Optional[str] = Field(None, max_length=200)
    reply_to: Optional[str] = Field(None, max_length=200)
    smtp: EmailSmtpConfig


class EmailSettingsOut(BaseModel):
    enabled: bool
    provider: str
    from_email: str
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    smtp: dict  # Without password
