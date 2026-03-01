"""Ecosystem 生态洞察 API 测试"""
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.ecosystem import EcosystemContributor, EcosystemProject
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
