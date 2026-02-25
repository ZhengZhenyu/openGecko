"""
Tests for upload API endpoints.

Endpoints tested:
- POST /api/upload/upload
- POST /api/upload/{content_id}/cover
"""
import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.content import Content
from app.services.storage import LocalStorage


@pytest.fixture(autouse=True)
def use_local_storage(tmp_path):
    """测试期间强制使用本地存储，避免依赖 boto3 / S3 配置"""
    storage = LocalStorage(str(tmp_path))
    with patch("app.api.upload.get_storage", return_value=storage):
        yield


class TestUploadFile:
    """Tests for POST /api/upload/upload"""

    def test_upload_markdown_file(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
        tmp_path,
    ):
        """Test uploading a markdown file creates content."""
        md_content = b"# Hello World\n\nThis is test content.\n"
        md_file = io.BytesIO(md_content)

        response = client.post(
            "/api/contents/upload",
            files={"file": ("test_article.md", md_file, "text/markdown")},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "test_article"
        assert "Hello World" in data["content_markdown"] or "Hello World" in data["content_html"]

    def test_upload_no_filename(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test uploading file with no filename returns 400."""
        empty_file = io.BytesIO(b"content")
        response = client.post(
            "/api/contents/upload",
            files={"file": ("", empty_file, "text/plain")},
            headers=auth_headers,
        )
        assert response.status_code in [400, 422]

    def test_upload_unsupported_file_type(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test uploading unsupported file type returns 400."""
        txt_file = io.BytesIO(b"plain text content")
        response = client.post(
            "/api/contents/upload",
            files={"file": ("file.txt", txt_file, "text/plain")},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_markdown_with_extension(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers: dict,
    ):
        """Test uploading .markdown extension (alternative to .md) works."""
        md_content = b"# Title\n\nParagraph text.\n"
        md_file = io.BytesIO(md_content)

        response = client.post(
            "/api/contents/upload",
            files={"file": ("article.markdown", md_file, "text/markdown")},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "article"


class TestUploadCoverImage:
    """Tests for POST /api/upload/{content_id}/cover"""

    def test_upload_cover_image_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test uploading a cover image for content."""
        content = Content(
            title="Test Content",
            content_markdown="Test",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        # Create a minimal valid JPEG header
        fake_jpg = b"\xff\xd8\xff\xe0" + b"\x00" * 100

        response = client.post(
            f"/api/contents/{content.id}/cover",
            files={"file": ("cover.jpg", io.BytesIO(fake_jpg), "image/jpeg")},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "/uploads/covers/" in data["cover_image"]
        assert data["cover_image"].endswith(".jpg")

    def test_upload_cover_image_nonexistent_content(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test uploading cover for non-existent content returns 404."""
        fake_jpg = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        response = client.post(
            "/api/contents/99999/cover",
            files={"file": ("cover.jpg", io.BytesIO(fake_jpg), "image/jpeg")},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_upload_cover_no_filename(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test uploading cover with no filename returns 400."""
        content = Content(
            title="Test Content",
            content_markdown="Test",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.post(
            f"/api/contents/{content.id}/cover",
            files={"file": ("", io.BytesIO(b"data"), "image/jpeg")},
            headers=auth_headers,
        )
        assert response.status_code in [400, 422]

    def test_upload_cover_unsupported_format(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test uploading unsupported image format returns 400."""
        content = Content(
            title="Test Content",
            content_markdown="Test",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.post(
            f"/api/contents/{content.id}/cover",
            files={"file": ("cover.bmp", io.BytesIO(b"bmp_data"), "image/bmp")},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "不支持的图片格式" in response.json()["detail"]

    def test_upload_cover_png_format(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test uploading PNG cover image succeeds."""
        content = Content(
            title="Test Content",
            content_markdown="Test",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        # Minimal PNG header
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            f"/api/contents/{content.id}/cover",
            files={"file": ("cover.png", io.BytesIO(fake_png), "image/png")},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cover_image"].endswith(".png")
