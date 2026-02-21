from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# JWT Configuration — single source from settings
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def encrypt_value(plain_text: str) -> str:
    """Encrypt a sensitive value for storage in the database.

    Uses Fernet symmetric encryption with the JWT secret key as the base.
    """
    if not plain_text:
        return ""
    import base64
    import hashlib

    from cryptography.fernet import Fernet

    # Derive a Fernet-compatible key from the JWT secret
    key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
    f = Fernet(key)
    return f.encrypt(plain_text.encode()).decode()


def decrypt_value(encrypted_text: str) -> str:
    """Decrypt a sensitive value from the database."""
    if not encrypted_text:
        return ""
    import base64
    import hashlib

    from cryptography.fernet import Fernet

    key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
    f = Fernet(key)
    return f.decrypt(encrypted_text.encode()).decode()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

