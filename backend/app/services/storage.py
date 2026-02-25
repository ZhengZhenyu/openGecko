"""StorageService abstraction — local filesystem or S3-compatible (MinIO / AWS S3)."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from pathlib import Path


class StorageService(ABC):
    @abstractmethod
    def save(self, data: bytes, key: str) -> str:
        """Save file data under *key* and return the public URL path (e.g. /uploads/covers/abc.jpg)."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete the object identified by *key* (relative path, e.g. covers/abc.jpg)."""

    @staticmethod
    def generate_key(ext: str, prefix: str = "") -> str:
        """Generate a unique storage key. *ext* should include the dot (e.g. '.jpg')."""
        name = f"{uuid.uuid4().hex}{ext}"
        return f"{prefix}/{name}" if prefix else name


class LocalStorage(StorageService):
    """Store files on the local filesystem under *upload_dir*."""

    def __init__(self, upload_dir: str) -> None:
        self.upload_dir = Path(upload_dir)

    def save(self, data: bytes, key: str) -> str:
        path = self.upload_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"/uploads/{key}"

    def delete(self, key: str) -> None:
        path = self.upload_dir / key
        if path.exists():
            path.unlink()


class S3Storage(StorageService):
    """Store files in an S3-compatible object store (MinIO, AWS S3, Huawei OBS …)."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        public_url: str,
    ) -> None:
        import boto3  # lazy import — only required when S3 backend is active

        self.bucket = bucket
        self.public_url = public_url.rstrip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )
        # Ensure the bucket exists
        try:
            self.client.head_bucket(Bucket=bucket)
        except Exception:
            self.client.create_bucket(Bucket=bucket)

    def save(self, data: bytes, key: str) -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)
        # Return the same /uploads/<key> path — nginx proxies this to MinIO
        return f"/uploads/{key}"

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


def get_storage() -> StorageService:
    """Factory: return the configured StorageService instance."""
    from app.config import settings  # deferred to avoid circular imports

    if settings.STORAGE_BACKEND == "s3":
        return S3Storage(
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            bucket=settings.S3_BUCKET,
            public_url=settings.S3_PUBLIC_URL,
        )
    return LocalStorage(settings.UPLOAD_DIR)
