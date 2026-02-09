"""
Tests for analytics and channel configuration API endpoints.

Endpoints tested:
- GET /api/analytics/overview
- GET /api/analytics/{content_id}
- GET /api/analytics/settings/channels
- PUT /api/analytics/settings/channels/{channel}
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.content import Content


class TestAnalyticsOverview:
    """Tests for GET /api/analytics/overview"""

    def test_overview_empty(
        self, client: TestClient, auth_headers: dict
    ):
        """Test analytics overview with no data."""
        response = client.get("/api/analytics/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_contents"] == 0
        assert data["total_published"] == 0
        assert data["channels"] == {}

    def test_overview_with_contents(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test analytics overview with content data."""
        # Create contents
        for i in range(5):
            content = Content(
                title=f"Content {i}",
                content_markdown="Test",
                content_html="<p>Test</p>",
                author="Author",
                status="draft" if i < 3 else "published",
                community_id=test_community.id,
                source_type="contribution",
            )
            db_session.add(content)
        db_session.commit()

        response = client.get("/api/analytics/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_contents"] == 5
        # Note: total_published counts publish records, not content status
        assert "channels" in data

    def test_overview_with_publish_records(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test analytics overview with publish records."""
        from app.models.publish_record import PublishRecord

        # Create content and publish records
        content = Content(
            title="Published Content",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        # Create publish records for different channels
        for channel in ["wechat", "hugo", "csdn"]:
            record = PublishRecord(
                content_id=content.id,
                channel=channel,
                status="published",
                community_id=test_community.id,
            )
            db_session.add(record)
        db_session.commit()

        response = client.get("/api/analytics/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_published"] == 3
        assert data["channels"]["wechat"] == 1
        assert data["channels"]["hugo"] == 1
        assert data["channels"]["csdn"] == 1

    def test_overview_filters_draft_status(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test overview doesn't count draft publish records."""
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

        # Create both draft and published records
        draft_record = PublishRecord(
            content_id=content.id,
            channel="wechat",
            status="draft",
            community_id=test_community.id,
        )
        published_record = PublishRecord(
            content_id=content.id,
            channel="hugo",
            status="published",
            community_id=test_community.id,
        )
        db_session.add_all([draft_record, published_record])
        db_session.commit()

        response = client.get("/api/analytics/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_published"] == 1  # Only published, not draft
        assert "wechat" not in data["channels"]  # Draft not counted
        assert data["channels"]["hugo"] == 1

    def test_overview_community_isolation(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_another_community: Community,
        auth_headers: dict,
    ):
        """Test analytics overview is isolated by community."""
        # Create content in test_community
        content1 = Content(
            title="My Content",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        # Create content in another_community
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

        response = client.get("/api/analytics/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should only count content from test_community
        assert data["total_contents"] == 1

    def test_overview_no_auth(self, client: TestClient):
        """Test analytics overview requires authentication."""
        response = client.get("/api/analytics/overview")
        assert response.status_code == 401


class TestContentAnalytics:
    """Tests for GET /api/analytics/{content_id}"""

    def test_content_analytics_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test getting analytics for specific content."""
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

        response = client.get(
            f"/api/analytics/{content.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content_id"] == content.id
        assert data["title"] == "Test Content"
        assert isinstance(data["analytics"], list)

    def test_content_analytics_with_records(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test content analytics includes publish records."""
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

        record = PublishRecord(
            content_id=content.id,
            channel="wechat",
            status="published",
            platform_article_id="12345",
            community_id=test_community.id,
        )
        db_session.add(record)
        db_session.commit()

        response = client.get(
            f"/api/analytics/{content.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["analytics"]) == 1
        assert data["analytics"][0]["channel"] == "wechat"
        assert data["analytics"][0]["status"] == "published"

    def test_content_analytics_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting analytics for non-existent content."""
        response = client.get("/api/analytics/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_content_analytics_from_another_community(
        self,
        client: TestClient,
        db_session: Session,
        test_another_community: Community,
        auth_headers: dict,
    ):
        """Test cannot get analytics for content from another community."""
        content = Content(
            title="Other Content",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_another_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.get(
            f"/api/analytics/{content.id}", headers=auth_headers
        )
        assert response.status_code == 404


class TestChannelSettings:
    """Tests for GET /api/analytics/settings/channels"""

    def test_get_channel_settings_empty(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting channel settings when none exist."""
        response = client.get(
            "/api/analytics/settings/channels", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should return default channels even if not in database
        assert len(data) >= 4  # wechat, hugo, csdn, zhihu
        channels = [c["channel"] for c in data]
        assert "wechat" in channels
        assert "hugo" in channels
        assert "csdn" in channels
        assert "zhihu" in channels

    def test_get_channel_settings_with_data(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test getting channel settings with existing data."""
        from app.models.channel import ChannelConfig

        config = ChannelConfig(
            channel="wechat",
            config={"app_id": "test123", "app_secret": "secret123"},
            enabled=True,
            community_id=test_community.id,
        )
        db_session.add(config)
        db_session.commit()

        response = client.get(
            "/api/analytics/settings/channels", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        wechat_config = next((c for c in data if c["channel"] == "wechat"), None)
        assert wechat_config is not None
        assert wechat_config["enabled"] is True
        assert "app_id" in wechat_config["config"]

    def test_get_channel_settings_no_auth(self, client: TestClient):
        """Test getting channel settings requires authentication."""
        response = client.get("/api/analytics/settings/channels")
        assert response.status_code == 401


class TestUpdateChannelSettings:
    """Tests for PUT /api/analytics/settings/channels/{channel}"""

    def test_update_channel_settings_create(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test creating channel settings."""
        response = client.put(
            "/api/analytics/settings/channels/wechat",
            headers=auth_headers,
            json={
                "config": {
                    "app_id": "wx123456",
                    "app_secret": "secret789",
                },
                "enabled": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "wechat"
        assert data["enabled"] is True
        assert data["config"]["app_id"] == "wx123456"

    def test_update_channel_settings_update_existing(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test updating existing channel settings."""
        from app.models.channel import ChannelConfig

        config = ChannelConfig(
            channel="hugo",
            config={"repo_path": "/old/path"},
            enabled=False,
            community_id=test_community.id,
        )
        db_session.add(config)
        db_session.commit()

        response = client.put(
            "/api/analytics/settings/channels/hugo",
            headers=auth_headers,
            json={
                "config": {"repo_path": "/new/path"},
                "enabled": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "hugo"
        assert data["enabled"] is True
        assert data["config"]["repo_path"] == "/new/path"

    def test_update_channel_settings_toggle_enabled(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test toggling channel enabled status."""
        from app.models.channel import ChannelConfig

        config = ChannelConfig(
            channel="csdn",
            config={},
            enabled=True,
            community_id=test_community.id,
        )
        db_session.add(config)
        db_session.commit()

        response = client.put(
            "/api/analytics/settings/channels/csdn",
            headers=auth_headers,
            json={"enabled": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False

    def test_update_channel_settings_invalid_channel(
        self, client: TestClient, auth_headers: dict
    ):
        """Test updating settings for invalid channel."""
        response = client.put(
            "/api/analytics/settings/channels/invalid_channel",
            headers=auth_headers,
            json={"enabled": True},
        )
        assert response.status_code == 400

    def test_update_channel_settings_community_isolation(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_another_community: Community,
        auth_headers: dict,
        another_user_auth_headers: dict,
    ):
        """Test channel settings are isolated by community."""
        from app.models.channel import ChannelConfig

        # User 1 creates config
        config1 = ChannelConfig(
            channel="wechat",
            config={"app_id": "user1_app"},
            enabled=True,
            community_id=test_community.id,
        )
        db_session.add(config1)
        db_session.commit()

        # User 2 creates their own config
        response = client.put(
            "/api/analytics/settings/channels/wechat",
            headers=another_user_auth_headers,
            json={
                "config": {"app_id": "user2_app"},
                "enabled": True,
            },
        )
        assert response.status_code == 200

        # User 1's config should still have their app_id
        response = client.get(
            "/api/analytics/settings/channels", headers=auth_headers
        )
        wechat_config = next(
            (c for c in response.json() if c["channel"] == "wechat"), None
        )
        assert wechat_config["config"]["app_id"] == "user1_app"

        # User 2's config should have their app_id
        response = client.get(
            "/api/analytics/settings/channels", headers=another_user_auth_headers
        )
        wechat_config = next(
            (c for c in response.json() if c["channel"] == "wechat"), None
        )
        assert wechat_config["config"]["app_id"] == "user2_app"
