"""
Tests for WechatService with mocked external API calls.

Uses pytest-httpx for mocking httpx requests to WeChat API.
"""

import re
import pytest
from unittest.mock import patch
from pathlib import Path
import tempfile
import os

from app.services.wechat import WechatService, wechat_service


@pytest.fixture
def mock_channel_config(db_session, test_community):
    """Create a mock WeChat channel config with encrypted credentials."""
    from app.models.channel import ChannelConfig
    from app.core.security import encrypt_value

    config = ChannelConfig(
        channel="wechat",
        config={
            "app_id": "wx1234567890",
            "app_secret": encrypt_value("test_secret_key_12345678"),
        },
        enabled=True,
        community_id=test_community.id,
    )
    db_session.add(config)
    db_session.commit()
    return config


@pytest.fixture
def mock_session_local(db_session):
    """Mock SessionLocal to return test database session."""
    with patch('app.database.SessionLocal') as mock:
        # Return test session but don't close it (fixture will handle that)
        mock_session = db_session
        mock.return_value = mock_session
        # Override close method to do nothing (fixture manages session lifecycle)
        mock_session.close = lambda: None
        yield mock
    # Restore original close method
    if hasattr(db_session, 'close'):
        delattr(db_session, 'close')


class TestWechatServiceCredentials:
    """Tests for credential loading and access token management."""

    def test_load_credentials_success(self, db_session, test_community, mock_channel_config, mock_session_local):
        """Test loading credentials from database."""
        service = WechatService()
        app_id, app_secret = service._load_credentials(test_community.id)

        assert app_id == "wx1234567890"
        assert app_secret == "test_secret_key_12345678"

    def test_load_credentials_missing_config(self, db_session, test_community, mock_session_local):
        """Test loading credentials when config doesn't exist."""
        service = WechatService()

        with pytest.raises(ValueError, match="微信公众号未配置"):
            service._load_credentials(test_community.id)

    def test_load_credentials_missing_app_id(self, db_session, test_community, mock_session_local):
        """Test loading credentials when app_id is missing."""
        from app.models.channel import ChannelConfig
        from app.core.security import encrypt_value

        config = ChannelConfig(
            channel="wechat",
            config={
                "app_secret": encrypt_value("secret123"),
            },
            enabled=True,
            community_id=test_community.id,
        )
        db_session.add(config)
        db_session.commit()

        service = WechatService()
        with pytest.raises(ValueError, match="AppID 或 AppSecret 未配置"):
            service._load_credentials(test_community.id)

    @pytest.mark.asyncio
    async def test_get_access_token_success(
        self, db_session, test_community, mock_channel_config, mock_session_local, httpx_mock
    ):
        """Test getting access token from WeChat API."""
        # Mock WeChat token API response
        httpx_mock.add_response(
            url="https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx1234567890&secret=test_secret_key_12345678",
            json={
                "access_token": "mock_access_token_123",
                "expires_in": 7200,
            }
        )

        service = WechatService()
        token = await service._get_access_token(test_community.id)

        assert token == "mock_access_token_123"
        assert service._token_cache[test_community.id]["token"] == "mock_access_token_123"

    @pytest.mark.asyncio
    async def test_get_access_token_cached(
        self, db_session, test_community, mock_channel_config, mock_session_local, httpx_mock
    ):
        """Test that access token is cached and not re-fetched."""
        httpx_mock.add_response(
            json={"access_token": "cached_token", "expires_in": 7200}
        )

        service = WechatService()
        token1 = await service._get_access_token(test_community.id)
        token2 = await service._get_access_token(test_community.id)

        assert token1 == token2
        # Should only make one request due to caching
        assert len(httpx_mock.get_requests()) == 1

    @pytest.mark.asyncio
    async def test_get_access_token_api_error(
        self, db_session, test_community, mock_channel_config, mock_session_local, httpx_mock
    ):
        """Test handling of WeChat API error when getting token."""
        httpx_mock.add_response(
            json={
                "errcode": 40001,
                "errmsg": "invalid credential"
            }
        )

        service = WechatService()
        with pytest.raises(Exception, match="获取access_token失败.*errcode=40001"):
            await service._get_access_token(test_community.id)


class TestWechatServiceImageUpload:
    """Tests for image upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_image_success(
        self, db_session, test_community, mock_channel_config, mock_session_local, httpx_mock
    ):
        """Test successful image upload to WeChat."""
        import re

        # Mock token API
        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/token\?.*"),
            json={"access_token": "test_token", "expires_in": 7200}
        )

        # Mock image upload API
        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/media/uploadimg\?.*"),
            json={"url": "https://mmbiz.qpic.cn/test_image.jpg"}
        )

        # Create a temporary test image
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image data")
            tmp_path = tmp.name

        try:
            service = WechatService()
            wechat_url = await service.upload_image(tmp_path, test_community.id)

            assert wechat_url == "https://mmbiz.qpic.cn/test_image.jpg"
        finally:
            os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_upload_image_api_error(
        self, db_session, test_community, mock_channel_config, mock_session_local, httpx_mock
    ):
        """Test handling of WeChat API error during image upload."""
        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/token\?.*"),
            json={"access_token": "test_token", "expires_in": 7200}
        )

        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/media/uploadimg\?.*"),
            json={
                "errcode": 40007,
                "errmsg": "invalid media_id"
            }
        )

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake image")
            tmp_path = tmp.name

        try:
            service = WechatService()
            with pytest.raises(Exception, match="微信图片上传失败.*errcode=40007"):
                await service.upload_image(tmp_path, test_community.id)
        finally:
            os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_upload_thumb_media_success(
        self, db_session, test_community, mock_channel_config, mock_session_local, httpx_mock
    ):
        """Test successful cover image upload."""
        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/token\?.*"),
            json={"access_token": "test_token", "expires_in": 7200}
        )

        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/material/add_material\?.*"),
            json={"media_id": "test_media_id_12345"}
        )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"fake cover image")
            tmp_path = tmp.name

        try:
            service = WechatService()
            media_id = await service.upload_thumb_media(tmp_path, test_community.id)

            assert media_id == "test_media_id_12345"
        finally:
            os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_upload_thumb_media_api_error(
        self, db_session, test_community, mock_channel_config, mock_session_local, httpx_mock
    ):
        """Test handling of WeChat API error during thumb upload."""
        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/token\?.*"),
            json={"access_token": "test_token", "expires_in": 7200}
        )

        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/material/add_material\?.*"),
            json={
                "errcode": 45001,
                "errmsg": "media size out of limit"
            }
        )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"fake cover")
            tmp_path = tmp.name

        try:
            service = WechatService()
            with pytest.raises(Exception, match="微信封面上传失败.*errcode=45001"):
                await service.upload_thumb_media(tmp_path, test_community.id)
        finally:
            os.unlink(tmp_path)


class TestWechatServiceDraftCreation:
    """Tests for draft creation functionality."""

    @pytest.mark.asyncio
    async def test_create_draft_success(
        self, db_session, test_community, mock_channel_config, mock_session_local, httpx_mock
    ):
        """Test successful draft creation."""
        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/token\?.*"),
            json={"access_token": "test_token", "expires_in": 7200}
        )

        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/draft/add\?.*"),
            json={"media_id": "draft_media_id_999"}
        )

        service = WechatService()
        result = await service.create_draft(
            title="测试文章",
            content_html="<p>测试内容</p>",
            author="测试作者",
            thumb_media_id="cover_123",
            community_id=test_community.id,
        )

        assert result["media_id"] == "draft_media_id_999"
        assert result["status"] == "draft"

    @pytest.mark.asyncio
    async def test_create_draft_api_error(
        self, db_session, test_community, mock_channel_config, mock_session_local, httpx_mock
    ):
        """Test handling of WeChat API error during draft creation."""
        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/token\?.*"),
            json={"access_token": "test_token", "expires_in": 7200}
        )

        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/draft/add\?.*"),
            json={
                "errcode": 40007,
                "errmsg": "invalid media_id"
            }
        )

        service = WechatService()
        with pytest.raises(Exception, match="微信草稿创建失败.*errcode=40007"):
            await service.create_draft(
                title="测试",
                content_html="<p>内容</p>",
                author="作者",
                thumb_media_id="invalid",
                community_id=test_community.id,
            )


class TestWechatServiceImageReplacement:
    """Tests for replacing local images with WeChat URLs."""

    @pytest.mark.asyncio
    async def test_replace_local_images_success(
        self, db_session, test_community, mock_channel_config, mock_session_local, httpx_mock
    ):
        """Test replacing local images with WeChat URLs."""
        from app.config import settings

        # Mock token and upload APIs
        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/token\?.*"),
            json={"access_token": "test_token", "expires_in": 7200}
        )
        httpx_mock.add_response(
            url=re.compile(r"https://api\.weixin\.qq\.com/cgi-bin/media/uploadimg\?.*"),
            json={"url": "https://mmbiz.qpic.cn/uploaded_image_1.jpg"}
        )

        # Create a temporary test image
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False, dir=settings.UPLOAD_DIR) as tmp:
            tmp.write(b"fake image data")
            tmp_name = os.path.basename(tmp.name)
            tmp_path = tmp.name

        try:
            markdown = f"# 标题\n\n![测试图片](/uploads/{tmp_name})\n\n内容文字"
            service = WechatService()
            result = await service._replace_local_images_with_wechat_urls(
                markdown, test_community.id
            )

            assert "https://mmbiz.qpic.cn/uploaded_image_1.jpg" in result
            assert f"/uploads/{tmp_name}" not in result
            assert "测试图片" in result
        finally:
            os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_replace_local_images_skip_external(
        self, db_session, test_community, mock_channel_config, mock_session_local
    ):
        """Test that external images are not uploaded."""
        markdown = "![外部图片](https://example.com/image.jpg)"
        service = WechatService()
        result = await service._replace_local_images_with_wechat_urls(
            markdown, test_community.id
        )

        # External image should remain unchanged
        assert "https://example.com/image.jpg" in result
        assert markdown == result

    @pytest.mark.asyncio
    async def test_replace_local_images_missing_file(
        self, db_session, test_community, mock_channel_config, mock_session_local
    ):
        """Test handling of missing image files."""
        markdown = "![缺失图片](/uploads/nonexistent.jpg)"
        service = WechatService()
        result = await service._replace_local_images_with_wechat_urls(
            markdown, test_community.id
        )

        # Missing image should remain unchanged
        assert "/uploads/nonexistent.jpg" in result
        assert markdown == result


class TestWechatServiceMarkdownConversion:
    """Tests for Markdown to WeChat HTML conversion."""

    def test_convert_to_wechat_html_basic(self):
        """Test basic Markdown conversion."""
        service = WechatService()
        markdown = "# 标题\n\n这是一段文字。"
        html = service.convert_to_wechat_html(markdown)

        assert "<h1" in html
        assert "style=" in html  # Should have inline styles
        assert "标题" in html
        assert "这是一段文字" in html

    def test_convert_to_wechat_html_code_blocks(self):
        """Test code block styling."""
        service = WechatService()
        markdown = "```python\nprint('hello')\n```"
        html = service.convert_to_wechat_html(markdown)

        assert "<pre" in html or "<code" in html
        assert "style=" in html
        assert "print" in html

    def test_convert_to_wechat_html_lists(self):
        """Test list conversion."""
        service = WechatService()
        markdown = "- 项目1\n- 项目2\n- 项目3"
        html = service.convert_to_wechat_html(markdown)

        assert "<ul" in html
        assert "<li" in html
        assert "style=" in html
        assert "项目1" in html

    def test_convert_to_wechat_html_blockquote(self):
        """Test blockquote styling."""
        service = WechatService()
        markdown = "> 这是引用内容"
        html = service.convert_to_wechat_html(markdown)

        assert "<blockquote" in html
        assert "style=" in html
        assert "这是引用内容" in html

    def test_convert_to_wechat_html_inline_code(self):
        """Test inline code styling."""
        service = WechatService()
        markdown = "使用 `print()` 函数输出"
        html = service.convert_to_wechat_html(markdown)

        assert "<code" in html
        assert "style=" in html
        assert "print()" in html

    def test_convert_to_wechat_html_table(self):
        """Test table conversion."""
        service = WechatService()
        markdown = """
| 列1 | 列2 |
|-----|-----|
| A   | B   |
| C   | D   |
"""
        html = service.convert_to_wechat_html(markdown)

        assert "<table" in html
        assert "<th" in html
        assert "<td" in html
        assert "style=" in html
        assert "列1" in html

    def test_convert_to_wechat_html_links(self):
        """Test link styling."""
        service = WechatService()
        markdown = "[点击这里](https://example.com)"
        html = service.convert_to_wechat_html(markdown)

        assert "<a" in html
        assert 'href="https://example.com"' in html
        assert "style=" in html
        assert "点击这里" in html
