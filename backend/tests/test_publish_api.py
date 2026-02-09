"""
Tests for publish management API endpoints.

Endpoints tested:
- POST /api/publish/{content_id}/wechat
- POST /api/publish/{content_id}/hugo
- GET /api/publish/{content_id}/preview/{channel}
- GET /api/publish/{content_id}/copy/{channel}
- GET /api/publish/records
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.content import Content


class TestPublishRecords:
    """Tests for GET /api/publish/records"""

    def test_list_publish_records_empty(
        self, client: TestClient, auth_headers: dict
    ):
        """Test listing publish records when none exist."""
        response = client.get("/api/publish/records", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_publish_records_with_data(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test listing publish records with existing data."""
        from app.models.publish_record import PublishRecord

        # Create test content and publish records
        content = Content(
            title="Test Content",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        record = PublishRecord(
            content_id=content.id,
            channel="wechat",
            status="published",
            platform_article_id="12345",
            community_id=test_community.id,
        )
        db_session.add(record)
        db_session.commit()

        response = client.get("/api/publish/records", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert data["items"][0]["channel"] == "wechat"
        assert data["items"][0]["status"] == "published"

    def test_list_publish_records_filter_by_content(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test filtering publish records by content_id."""
        from app.models.publish_record import PublishRecord

        content1 = Content(
            title="Content 1",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        content2 = Content(
            title="Content 2",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add_all([content1, content2])
        db_session.commit()

        record1 = PublishRecord(
            content_id=content1.id,
            channel="wechat",
            status="published",
            community_id=test_community.id,
        )
        record2 = PublishRecord(
            content_id=content2.id,
            channel="hugo",
            status="published",
            community_id=test_community.id,
        )
        db_session.add_all([record1, record2])
        db_session.commit()

        response = client.get(
            f"/api/publish/records?content_id={content1.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["content_id"] == content1.id

    def test_list_publish_records_filter_by_channel(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test filtering publish records by channel."""
        from app.models.publish_record import PublishRecord

        content = Content(
            title="Test",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        for channel in ["wechat", "hugo", "csdn"]:
            record = PublishRecord(
                content_id=content.id,
                channel=channel,
                status="published",
                community_id=test_community.id,
            )
            db_session.add(record)
        db_session.commit()

        response = client.get(
            "/api/publish/records?channel=wechat", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["channel"] == "wechat" for item in data["items"])

    def test_list_publish_records_community_isolation(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_another_community: Community,
        auth_headers: dict,
    ):
        """Test publish records are isolated by community."""
        from app.models.publish_record import PublishRecord

        content1 = Content(
            title="My Content",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        content2 = Content(
            title="Other Content",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_another_community.id,
            source_type="contribution",
        )
        db_session.add_all([content1, content2])
        db_session.commit()

        record1 = PublishRecord(
            content_id=content1.id,
            channel="wechat",
            status="published",
            community_id=test_community.id,
        )
        record2 = PublishRecord(
            content_id=content2.id,
            channel="wechat",
            status="published",
            community_id=test_another_community.id,
        )
        db_session.add_all([record1, record2])
        db_session.commit()

        response = client.get("/api/publish/records", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should only see records from test_community
        assert all(
            item["content_id"] == content1.id for item in data["items"]
        )


class TestPreviewContent:
    """Tests for GET /api/publish/{content_id}/preview/{channel}"""

    def test_preview_wechat(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test previewing content in WeChat format."""
        content = Content(
            title="Test Content",
            content_markdown="# Hello\n\nThis is a test.",
            content_html="<h1>Hello</h1><p>This is a test.</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.get(
            f"/api/publish/{content.id}/preview/wechat", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Content"
        assert "formatted_content" in data
        assert data["channel"] == "wechat"

    def test_preview_hugo(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test previewing content in Hugo format."""
        content = Content(
            title="Hugo Post",
            content_markdown="# Title\n\nContent here.",
            content_html="<h1>Title</h1><p>Content here.</p>",
            author="Author",
            tags=["python", "tutorial"],
            category="Programming",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.get(
            f"/api/publish/{content.id}/preview/hugo", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Hugo Post"
        assert "---" in data["formatted_content"]  # Hugo frontmatter
        assert "python" in data["formatted_content"]  # Tags
        assert data["channel"] == "hugo"

    def test_preview_invalid_channel(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test previewing with invalid channel returns error."""
        content = Content(
            title="Test",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.get(
            f"/api/publish/{content.id}/preview/invalid_channel",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_preview_nonexistent_content(
        self, client: TestClient, auth_headers: dict
    ):
        """Test previewing non-existent content returns 404."""
        response = client.get(
            "/api/publish/99999/preview/wechat", headers=auth_headers
        )
        assert response.status_code == 404


class TestCopyContent:
    """Tests for GET /api/publish/{content_id}/copy/{channel}"""

    def test_copy_csdn(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test getting copyable content for CSDN."""
        content = Content(
            title="CSDN Article",
            content_markdown="# Article\n\nContent for CSDN.",
            content_html="<h1>Article</h1><p>Content for CSDN.</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.get(
            f"/api/publish/{content.id}/copy/csdn", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "CSDN Article"
        assert "copyable_content" in data
        assert data["channel"] == "csdn"

    def test_copy_zhihu(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test getting copyable content for Zhihu."""
        content = Content(
            title="Zhihu Article",
            content_markdown="# Article\n\nContent for Zhihu.",
            content_html="<h1>Article</h1><p>Content for Zhihu.</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.get(
            f"/api/publish/{content.id}/copy/zhihu", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Zhihu Article"
        assert "copyable_content" in data
        assert data["channel"] == "zhihu"

    def test_copy_invalid_channel(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test copy with invalid channel returns error."""
        content = Content(
            title="Test",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.get(
            f"/api/publish/{content.id}/copy/wechat",  # wechat not supported for copy
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_copy_nonexistent_content(
        self, client: TestClient, auth_headers: dict
    ):
        """Test copying non-existent content returns 404."""
        response = client.get(
            "/api/publish/99999/copy/csdn", headers=auth_headers
        )
        assert response.status_code == 404


class TestPublishToWechat:
    """Tests for POST /api/publish/{content_id}/wechat"""

    def test_publish_to_wechat_missing_config(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test publishing to WeChat without configuration returns error."""
        content = Content(
            title="Test",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.post(
            f"/api/publish/{content.id}/wechat", headers=auth_headers
        )
        # Should return error due to missing WeChat configuration
        assert response.status_code in [400, 500]

    def test_publish_to_wechat_nonexistent_content(
        self, client: TestClient, auth_headers: dict
    ):
        """Test publishing non-existent content returns 404."""
        response = client.post(
            "/api/publish/99999/wechat", headers=auth_headers
        )
        assert response.status_code == 404


class TestPublishToHugo:
    """Tests for POST /api/publish/{content_id}/hugo"""

    def test_publish_to_hugo_missing_config(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test publishing to Hugo without configuration returns error."""
        content = Content(
            title="Test",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.post(
            f"/api/publish/{content.id}/hugo", headers=auth_headers
        )
        # Should return error due to missing Hugo configuration
        assert response.status_code in [400, 500]

    def test_publish_to_hugo_nonexistent_content(
        self, client: TestClient, auth_headers: dict
    ):
        """Test publishing non-existent content returns 404."""
        response = client.post(
            "/api/publish/99999/hugo", headers=auth_headers
        )
        assert response.status_code == 404
