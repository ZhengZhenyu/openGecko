"""Ecosystem 生态洞察 API 测试"""
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.ecosystem import EcosystemContributor, EcosystemProject, EcosystemSnapshot
from app.models.people import PersonProfile


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def test_project(db_session: Session, test_community, test_user):
    project = EcosystemProject(
        community_id=test_community.id,
        added_by_id=test_user.id,
        name="openGecko",
        platform="github",
        org_name="opensourceways",
        repo_name="openGecko",
        description="测试项目",
        tags=["python", "fastapi"],
        is_active=True,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_contributor(db_session: Session, test_project):
    contributor = EcosystemContributor(
        project_id=test_project.id,
        github_handle="octocat",
        display_name="Octocat",
        avatar_url="https://github.com/octocat.png",
        commit_count_90d=42,
    )
    db_session.add(contributor)
    db_session.commit()
    db_session.refresh(contributor)
    return contributor


# ─── Project CRUD ─────────────────────────────────────────────────────────────

class TestListProjects:
    def test_list_projects_empty(self, client: TestClient, auth_headers):
        resp = client.get("/api/ecosystem", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_projects_returns_data(self, client: TestClient, auth_headers, test_project):
        resp = client.get("/api/ecosystem", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "openGecko"

    def test_list_projects_cross_community(self, client: TestClient, another_user_auth_headers, test_project):
        """生态项目采用 community association 模式，跨社区用户也可看到项目列表"""
        resp = client.get("/api/ecosystem", headers=another_user_auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestCreateProject:
    def test_create_project_success(self, client: TestClient, auth_headers):
        resp = client.post("/api/ecosystem", headers=auth_headers, json={
            "name": "新项目",
            "platform": "github",
            "org_name": "testorg",
            "repo_name": "testrepo",
            "description": "描述",
            "tags": ["python"],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "新项目"
        assert data["platform"] == "github"

    def test_create_project_invalid_platform(self, client: TestClient, auth_headers):
        resp = client.post("/api/ecosystem", headers=auth_headers, json={
            "name": "项目",
            "platform": "invalid",
            "org_name": "org",
        })
        assert resp.status_code == 400

    def test_create_project_gitee(self, client: TestClient, auth_headers):
        resp = client.post("/api/ecosystem", headers=auth_headers, json={
            "name": "Gitee项目",
            "platform": "gitee",
            "org_name": "testorg",
        })
        assert resp.status_code == 201


class TestGetProject:
    def test_get_project_success(self, client: TestClient, auth_headers, test_project):
        resp = client.get(f"/api/ecosystem/{test_project.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "openGecko"

    def test_get_project_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/ecosystem/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_project_cross_community_accessible(self, client: TestClient, another_user_auth_headers, test_project):
        """生态项目采用 community association 模式，跨社区用户可访问项目详情"""
        resp = client.get(f"/api/ecosystem/{test_project.id}", headers=another_user_auth_headers)
        assert resp.status_code == 200


class TestUpdateProject:
    def test_update_project_success(self, client: TestClient, auth_headers, test_project):
        resp = client.patch(f"/api/ecosystem/{test_project.id}", headers=auth_headers, json={
            "description": "新描述",
            "is_active": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "新描述"
        assert data["is_active"] is False

    def test_update_project_not_found(self, client: TestClient, auth_headers):
        resp = client.patch("/api/ecosystem/99999", headers=auth_headers, json={"description": "x"})
        assert resp.status_code == 404


# ─── Sync ─────────────────────────────────────────────────────────────────────

class TestSyncProject:
    def test_sync_project_success(self, client: TestClient, auth_headers, test_project):
        mock_result = {"created": 5, "updated": 2, "errors": 0}
        with mock.patch("app.api.ecosystem.sync_project", return_value=mock_result):
            resp = client.post(f"/api/ecosystem/{test_project.id}/sync", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 5
        assert data["updated"] == 2

    def test_sync_project_not_found(self, client: TestClient, auth_headers):
        resp = client.post("/api/ecosystem/99999/sync", headers=auth_headers)
        assert resp.status_code == 404


# ─── Contributors ─────────────────────────────────────────────────────────────

class TestListContributors:
    def test_list_contributors_empty(self, client: TestClient, auth_headers, test_project):
        resp = client.get(f"/api/ecosystem/{test_project.id}/contributors", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_contributors_with_data(self, client: TestClient, auth_headers, test_project, test_contributor):
        resp = client.get(f"/api/ecosystem/{test_project.id}/contributors", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["github_handle"] == "octocat"

    def test_list_contributors_search(self, client: TestClient, auth_headers, test_project, test_contributor):
        resp = client.get(f"/api/ecosystem/{test_project.id}/contributors?q=octo", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        resp2 = client.get(f"/api/ecosystem/{test_project.id}/contributors?q=nomatch", headers=auth_headers)
        assert resp2.status_code == 200
        assert resp2.json()["total"] == 0

    def test_list_contributors_unlinked_filter(self, client: TestClient, auth_headers, test_project, test_contributor):
        resp = client.get(f"/api/ecosystem/{test_project.id}/contributors?unlinked=true", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_contributors_project_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/ecosystem/99999/contributors", headers=auth_headers)
        assert resp.status_code == 404


# ─── Import Contributor to People ─────────────────────────────────────────────

class TestImportContributorToPeople:
    def test_import_creates_new_person(self, client: TestClient, auth_headers, test_project, test_contributor):
        resp = client.post(
            f"/api/ecosystem/{test_project.id}/contributors/octocat/import-person",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "created"
        assert "person_id" in data

    def test_import_links_existing_person(self, client: TestClient, auth_headers, test_project, test_contributor, db_session: Session):
        # 先创建已有人脉档案
        existing_person = PersonProfile(
            display_name="Octocat",
            github_handle="octocat",
            source="manual",
        )
        db_session.add(existing_person)
        db_session.commit()

        resp = client.post(
            f"/api/ecosystem/{test_project.id}/contributors/octocat/import-person",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "linked"
        assert data["person_id"] == existing_person.id

    def test_import_contributor_not_found(self, client: TestClient, auth_headers, test_project):
        resp = client.post(
            f"/api/ecosystem/{test_project.id}/contributors/no-such-user/import-person",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_import_project_not_found(self, client: TestClient, auth_headers):
        resp = client.post(
            "/api/ecosystem/99999/contributors/someuser/import-person",
            headers=auth_headers,
        )
        assert resp.status_code == 404


# ─── Auto Sync Config ─────────────────────────────────────────────────────────

class TestAutoSyncConfig:
    def test_create_project_default_auto_sync(self, client: TestClient, auth_headers):
        """创建项目时，auto_sync_enabled 默认为 True，sync_interval_hours 默认为 None"""
        resp = client.post("/api/ecosystem", headers=auth_headers, json={
            "name": "默认采集项目",
            "platform": "github",
            "org_name": "defaultorg",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["auto_sync_enabled"] is True
        assert data["sync_interval_hours"] is None

    def test_create_project_auto_sync_disabled(self, client: TestClient, auth_headers):
        """创建项目时可以显式关闭自动采集"""
        resp = client.post("/api/ecosystem", headers=auth_headers, json={
            "name": "无采集项目",
            "platform": "github",
            "org_name": "nosynorg",
            "auto_sync_enabled": False,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["auto_sync_enabled"] is False
        assert data["sync_interval_hours"] is None

    def test_create_project_with_custom_interval(self, client: TestClient, auth_headers):
        """创建项目时可以指定自定义采集间隔"""
        resp = client.post("/api/ecosystem", headers=auth_headers, json={
            "name": "自定义间隔项目",
            "platform": "github",
            "org_name": "intervalorg",
            "auto_sync_enabled": True,
            "sync_interval_hours": 48,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["auto_sync_enabled"] is True
        assert data["sync_interval_hours"] == 48

    def test_update_auto_sync_config(self, client: TestClient, auth_headers, test_project):
        """PATCH 可以更新 auto_sync_enabled 和 sync_interval_hours"""
        resp = client.patch(f"/api/ecosystem/{test_project.id}", headers=auth_headers, json={
            "auto_sync_enabled": False,
            "sync_interval_hours": 12,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["auto_sync_enabled"] is False
        assert data["sync_interval_hours"] == 12

    def test_update_auto_sync_reset_interval(self, client: TestClient, auth_headers, test_project):
        """sync_interval_hours 可以被重置为 None（使用全局默认值）"""
        # 先设置间隔
        client.patch(f"/api/ecosystem/{test_project.id}", headers=auth_headers, json={
            "sync_interval_hours": 24,
        })
        # 再重置为 None
        resp = client.patch(f"/api/ecosystem/{test_project.id}", headers=auth_headers, json={
            "sync_interval_hours": None,
        })
        assert resp.status_code == 200
        assert resp.json()["sync_interval_hours"] is None

    def test_list_projects_includes_sync_config(self, client: TestClient, auth_headers, test_project):
        """列表接口也应包含 auto_sync_enabled 和 sync_interval_hours 字段"""
        resp = client.get("/api/ecosystem", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        item = next(p for p in data if p["id"] == test_project.id)
        assert "auto_sync_enabled" in item
        assert "sync_interval_hours" in item


# ─── Crawler Snapshot & Profile Enrichment ────────────────────────────────────

def _make_httpx_response(status_code: int, json_data):
    """构造 mock httpx.Response 对象。"""
    resp = mock.MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


def _make_contributors_response():
    """返回 /contributors API 的示例数据。"""
    return [
        {"login": "alice", "contributions": 80, "avatar_url": "https://github.com/alice.png"},
    ]


def _make_repo_stats_response():
    return {
        "stargazers_count": 500,
        "forks_count": 50,
        "open_issues_count": 10,
    }


def _make_commit_activity_response():
    """52 周数据，最后 4 周各有 5 commits。"""
    weeks = [{"total": 0, "week": i * 604800} for i in range(48)]
    weeks += [{"total": 5, "week": (48 + i) * 604800} for i in range(4)]
    return weeks


def _make_contributor_stats_response():
    """返回单个全量贡献者统计（active 近 4 周有 commit）。"""
    now_ts = int(datetime.now(timezone.utc).timestamp())
    recent_week_ts = now_ts - 7 * 24 * 3600
    old_week_ts = now_ts - 100 * 24 * 3600
    return [
        {
            "author": {"login": "alice"},
            "weeks": [
                {"w": old_week_ts, "c": 0},
                {"w": recent_week_ts, "c": 3},
            ],
        }
    ]


def _make_pulls_response():
    now = datetime.now(timezone.utc)
    return [
        {"merged_at": (now - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")},
        {"merged_at": None},
    ]


def _make_user_profile_response():
    return {"company": "OpenSource Inc", "location": "Beijing"}


def _build_mock_client(contributors_resp, profile_resp=None):
    """构造 mock httpx.Client，按 URL 分发不同响应。"""
    client_instance = mock.MagicMock()

    def fake_get(url, **kwargs):
        # 匹配顺序：由具体到通用
        if "/users/" in url:
            return _make_httpx_response(200, profile_resp or _make_user_profile_response())
        if "/contributors" in url and "stats" not in url:
            return _make_httpx_response(200, contributors_resp)
        if "stats/commit_activity" in url:
            return _make_httpx_response(200, _make_commit_activity_response())
        if "stats/contributors" in url:
            return _make_httpx_response(200, _make_contributor_stats_response())
        if "/pulls" in url:
            return _make_httpx_response(200, _make_pulls_response())
        if "/repos/" in url:
            # /repos/{org}/{repo} — 仓库基础数据（兜底）
            return _make_httpx_response(200, _make_repo_stats_response())
        return _make_httpx_response(404, {})

    client_instance.get.side_effect = fake_get
    # 支持 `with httpx.Client(...) as client:` 上下文管理器
    client_instance.__enter__ = mock.MagicMock(return_value=client_instance)
    client_instance.__exit__ = mock.MagicMock(return_value=False)
    return client_instance


class TestCrawlerSnapshot:
    """测试 github_crawler.sync_project() 快照写入与档案补充行为。"""

    def test_sync_creates_snapshot(self, db_session: Session, test_project):
        """同步后应写入一条 EcosystemSnapshot 记录。"""
        from app.services.ecosystem.github_crawler import sync_project

        mock_client = _build_mock_client(_make_contributors_response())

        with mock.patch("app.services.ecosystem.github_crawler.httpx.Client", return_value=mock_client):
            result = sync_project(db_session, test_project, token=None)

        assert result["errors"] == 0
        snapshot = (
            db_session.query(EcosystemSnapshot)
            .filter(EcosystemSnapshot.project_id == test_project.id)
            .first()
        )
        assert snapshot is not None
        assert snapshot.stars == 500
        assert snapshot.forks == 50

    def test_sync_snapshot_throttle(self, db_session: Session, test_project):
        """23h 内重复同步不应写入第二条快照。"""
        from app.services.ecosystem.github_crawler import sync_project

        mock_client = _build_mock_client(_make_contributors_response())

        with mock.patch("app.services.ecosystem.github_crawler.httpx.Client", return_value=mock_client):
            sync_project(db_session, test_project, token=None)
            # 第二次同步（距第一次不足 23h）
            sync_project(db_session, test_project, token=None)

        count = (
            db_session.query(EcosystemSnapshot)
            .filter(EcosystemSnapshot.project_id == test_project.id)
            .count()
        )
        assert count == 1

    def test_contributor_profile_enriched(self, db_session: Session, test_project):
        """新贡献者同步后应填充 company / location / first_contributed_at。"""
        from app.services.ecosystem.github_crawler import sync_project

        mock_client = _build_mock_client(_make_contributors_response())

        with mock.patch("app.services.ecosystem.github_crawler.httpx.Client", return_value=mock_client):
            result = sync_project(db_session, test_project, token=None)

        assert result["created"] == 1
        contributor = (
            db_session.query(EcosystemContributor)
            .filter(
                EcosystemContributor.project_id == test_project.id,
                EcosystemContributor.github_handle == "alice",
            )
            .first()
        )
        assert contributor is not None
        assert contributor.company == "OpenSource Inc"
        assert contributor.location == "Beijing"
        assert contributor.first_contributed_at is not None

    def test_sync_skips_profile_for_existing(self, db_session: Session, test_project):
        """已有贡献者（非新建）不应调用 /users/ API。"""
        from app.services.ecosystem.github_crawler import sync_project

        # 预先插入已存在的贡献者（无需 first_contributed_at）
        existing = EcosystemContributor(
            project_id=test_project.id,
            github_handle="alice",
            display_name="Alice",
            commit_count_90d=50,
        )
        db_session.add(existing)
        db_session.commit()

        mock_client = _build_mock_client(_make_contributors_response())

        with mock.patch("app.services.ecosystem.github_crawler.httpx.Client", return_value=mock_client):
            result = sync_project(db_session, test_project, token=None)

        # 已有贡献者 → updated=1, created=0
        assert result["updated"] == 1
        assert result["created"] == 0
        # /users/ 不应被调用
        for call_args in mock_client.get.call_args_list:
            url = call_args[0][0] if call_args[0] else call_args[1].get("url", "")
            assert "/users/" not in url

    def test_github_token_in_headers(self, db_session: Session, test_project):
        """指定 token 时，请求头中应包含 Authorization: Bearer xxx。"""
        from app.services.ecosystem.github_crawler import sync_project

        mock_client = _build_mock_client(_make_contributors_response())
        captured_headers: list[dict] = []

        original_side_effect = mock_client.get.side_effect

        def capturing_get(url, **kwargs):
            captured_headers.append(kwargs.get("headers", {}))
            return original_side_effect(url, **kwargs)

        mock_client.get.side_effect = capturing_get

        with mock.patch("app.services.ecosystem.github_crawler.httpx.Client", return_value=mock_client):
            sync_project(db_session, test_project, token="ghp_test_token")

        assert any("ghp_test_token" in h.get("Authorization", "") for h in captured_headers)


# ─── Sync Worker: get_projects_due() ──────────────────────────────────────────


class TestSyncWorkerDue:
    """测试 sync_worker.get_projects_due() 的到期判断逻辑。"""

    def _make_project(self, db: Session, test_community, test_user, **kwargs) -> EcosystemProject:
        defaults = {
            "community_id": test_community.id,
            "added_by_id": test_user.id,
            "name": "worker-test-project",
            "platform": "github",
            "org_name": "testorg",
            "repo_name": "testrepo",
            "is_active": True,
            "auto_sync_enabled": True,
        }
        defaults.update(kwargs)
        project = EcosystemProject(**defaults)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def test_get_projects_due_never_synced(self, db_session: Session, test_community, test_user):
        """last_synced_at 为 None 的项目应判定为到期。"""
        from app.services.ecosystem.sync_worker import get_projects_due

        project = self._make_project(db_session, test_community, test_user, last_synced_at=None)
        due = get_projects_due(db_session)
        assert any(p.id == project.id for p in due)

    def test_get_projects_due_recently_synced(self, db_session: Session, test_community, test_user):
        """刚刚同步过（未超过 sync_interval_hours）的项目不应到期。"""
        from app.services.ecosystem.sync_worker import get_projects_due

        just_now = datetime.now(timezone.utc)
        project = self._make_project(
            db_session, test_community, test_user,
            last_synced_at=just_now,
            sync_interval_hours=24,
        )
        due = get_projects_due(db_session)
        assert not any(p.id == project.id for p in due)

    def test_get_projects_due_auto_sync_disabled(self, db_session: Session, test_community, test_user):
        """auto_sync_enabled=False 的项目永远不应出现在到期列表中。"""
        from app.services.ecosystem.sync_worker import get_projects_due

        project = self._make_project(
            db_session, test_community, test_user,
            auto_sync_enabled=False,
            last_synced_at=None,
        )
        due = get_projects_due(db_session)
        assert not any(p.id == project.id for p in due)
