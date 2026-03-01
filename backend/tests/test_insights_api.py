"""生态情报 API 测试（/api/insights/*）"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.ecosystem import EcosystemContributor, EcosystemProject, EcosystemSnapshot


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def test_project(db_session: Session, test_community, test_user):
    project = EcosystemProject(
        community_id=test_community.id,
        added_by_id=test_user.id,
        name="testRepo",
        platform="github",
        org_name="testorg",
        repo_name="testrepo",
        is_active=True,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_project2(db_session: Session, test_community, test_user):
    """第二个项目，用于跨项目测试。"""
    project = EcosystemProject(
        community_id=test_community.id,
        added_by_id=test_user.id,
        name="anotherRepo",
        platform="github",
        org_name="testorg",
        repo_name="anotherrepo",
        is_active=True,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def make_snapshot(db_session: Session):
    """工厂 fixture：创建指定 project 的快照，offset_days 表示距今天数。"""
    def _factory(project, offset_days=0, **kwargs):
        snap = EcosystemSnapshot(
            project_id=project.id,
            snapshot_at=datetime.now(timezone.utc) - timedelta(days=offset_days),
            **kwargs,
        )
        db_session.add(snap)
        db_session.commit()
        db_session.refresh(snap)
        return snap
    return _factory


@pytest.fixture
def make_contributor(db_session: Session):
    """工厂 fixture：创建贡献者。"""
    def _factory(project, github_handle="octocat", **kwargs):
        c = EcosystemContributor(
            project_id=project.id,
            github_handle=github_handle,
            display_name=github_handle,
            **kwargs,
        )
        db_session.add(c)
        db_session.commit()
        db_session.refresh(c)
        return c
    return _factory


# ─── Trend ────────────────────────────────────────────────────────────────────


class TestTrendEndpoints:
    def test_list_trends_empty(self, client: TestClient, auth_headers, test_project):
        """无快照时返回 insufficient_data。"""
        resp = client.get("/api/insights/trends", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        item = next(d for d in data if d["project_id"] == test_project.id)
        assert item["momentum"] == "insufficient_data"
        assert item["snapshot_count"] == 0

    def test_list_trends_one_snapshot(self, client: TestClient, auth_headers, test_project, make_snapshot):
        """只有 1 个快照时仍返回 insufficient_data。"""
        make_snapshot(test_project, offset_days=0, stars=100, active_contributors_30d=5)
        resp = client.get("/api/insights/trends", headers=auth_headers)
        assert resp.status_code == 200
        item = next(d for d in resp.json() if d["project_id"] == test_project.id)
        assert item["momentum"] == "insufficient_data"
        assert item["snapshot_count"] == 1

    def test_list_trends_accelerating(self, client: TestClient, auth_headers, test_project, make_snapshot):
        """2 个快照，指标明显增长 → accelerating。"""
        make_snapshot(test_project, offset_days=30, stars=100, active_contributors_30d=5, pr_merged_30d=5, commits_30d=20)
        make_snapshot(test_project, offset_days=0, stars=150, active_contributors_30d=10, pr_merged_30d=10, commits_30d=40)
        resp = client.get("/api/insights/trends", headers=auth_headers)
        assert resp.status_code == 200
        item = next(d for d in resp.json() if d["project_id"] == test_project.id)
        assert item["momentum"] == "accelerating"
        assert item["velocity_score"] > 50
        assert item["snapshot_count"] == 2

    def test_list_trends_declining(self, client: TestClient, auth_headers, test_project, make_snapshot):
        """指标明显下降 → declining。"""
        make_snapshot(test_project, offset_days=30, stars=200, active_contributors_30d=20, pr_merged_30d=20, commits_30d=80)
        make_snapshot(test_project, offset_days=0, stars=190, active_contributors_30d=5, pr_merged_30d=3, commits_30d=10)
        resp = client.get("/api/insights/trends", headers=auth_headers)
        assert resp.status_code == 200
        item = next(d for d in resp.json() if d["project_id"] == test_project.id)
        assert item["momentum"] == "declining"

    def test_list_trends_growing(self, client: TestClient, auth_headers, test_project, make_snapshot):
        """指标适度增长（composite 0.05–0.20）→ growing。"""
        # 各指标约 +8–10% 增长，composite ≈ 0.089 → growing
        make_snapshot(test_project, offset_days=30, stars=100, active_contributors_30d=10, pr_merged_30d=10, commits_30d=20)
        make_snapshot(test_project, offset_days=0, stars=108, active_contributors_30d=11, pr_merged_30d=11, commits_30d=21)
        resp = client.get("/api/insights/trends", headers=auth_headers)
        assert resp.status_code == 200
        item = next(d for d in resp.json() if d["project_id"] == test_project.id)
        assert item["momentum"] == "growing"

    def test_list_trends_stable(self, client: TestClient, auth_headers, test_project, make_snapshot):
        """指标几乎无变化（composite -0.05–0.05）→ stable。"""
        # stars +2%，其余不变，composite ≈ 0.004 → stable
        make_snapshot(test_project, offset_days=30, stars=100, active_contributors_30d=10, pr_merged_30d=10, commits_30d=20)
        make_snapshot(test_project, offset_days=0, stars=102, active_contributors_30d=10, pr_merged_30d=10, commits_30d=20)
        resp = client.get("/api/insights/trends", headers=auth_headers)
        assert resp.status_code == 200
        item = next(d for d in resp.json() if d["project_id"] == test_project.id)
        assert item["momentum"] == "stable"

    def test_list_trends_filter_by_momentum(self, client: TestClient, auth_headers, test_project, make_snapshot):
        """momentum 查询参数过滤。"""
        make_snapshot(test_project, offset_days=30, stars=100, active_contributors_30d=5)
        make_snapshot(test_project, offset_days=0, stars=200, active_contributors_30d=15)
        resp = client.get("/api/insights/trends?momentum=insufficient_data", headers=auth_headers)
        assert resp.status_code == 200
        # 本项目是 accelerating，过滤后不应包含
        ids = [d["project_id"] for d in resp.json()]
        assert test_project.id not in ids

    def test_get_trend_project_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/insights/trends/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_trend_single_project(self, client: TestClient, auth_headers, test_project, make_snapshot):
        """单项目趋势详情。"""
        make_snapshot(test_project, offset_days=30, stars=100, active_contributors_30d=5)
        make_snapshot(test_project, offset_days=0, stars=130, active_contributors_30d=8)
        resp = client.get(f"/api/insights/trends/{test_project.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == test_project.id
        assert data["momentum"] in ["accelerating", "growing", "stable", "declining", "insufficient_data"]

    def test_trends_no_auth(self, client: TestClient):
        resp = client.get("/api/insights/trends")
        assert resp.status_code == 401


# ─── Influence ────────────────────────────────────────────────────────────────


class TestInfluenceEndpoints:
    def test_list_people_empty(self, client: TestClient, auth_headers):
        resp = client.get("/api/insights/people", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_people_basic(self, client: TestClient, auth_headers, test_project, make_contributor):
        make_contributor(test_project, github_handle="alice", commit_count_90d=100, pr_count_90d=20)
        resp = client.get("/api/insights/people", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        person = next(p for p in data if p["github_handle"] == "alice")
        assert "influence_score" in person
        assert "contributor" in person["influence_types"]

    def test_bridge_detection(self, client: TestClient, auth_headers, test_project, test_project2, make_contributor):
        """同一 handle 跨 2 个项目 → bridge。"""
        make_contributor(test_project, github_handle="bridge_user", commit_count_90d=30)
        make_contributor(test_project2, github_handle="bridge_user", commit_count_90d=30)
        resp = client.get("/api/insights/people", headers=auth_headers)
        assert resp.status_code == 200
        person = next(p for p in resp.json() if p["github_handle"] == "bridge_user")
        assert "bridge" in person["influence_types"]
        assert person["cross_project_count"] == 2

    def test_maintainer_detection(self, client: TestClient, auth_headers, test_project, make_contributor):
        make_contributor(test_project, github_handle="maintainer_user", role="maintainer", commit_count_90d=50)
        resp = client.get("/api/insights/people", headers=auth_headers)
        assert resp.status_code == 200
        person = next(p for p in resp.json() if p["github_handle"] == "maintainer_user")
        assert "maintainer" in person["influence_types"]

    def test_rising_star_detection(self, client: TestClient, auth_headers, test_project, make_contributor, db_session: Session):
        """first_contributed_at 在 90 天内且 commit ≥ 5 → rising_star。"""
        recent_date = datetime.now(timezone.utc) - timedelta(days=30)
        c = make_contributor(test_project, github_handle="newbie", commit_count_90d=10)
        c.first_contributed_at = recent_date
        db_session.commit()
        resp = client.get("/api/insights/people", headers=auth_headers)
        assert resp.status_code == 200
        person = next(p for p in resp.json() if p["github_handle"] == "newbie")
        assert "rising_star" in person["influence_types"]

    def test_reviewer_detection(self, client: TestClient, auth_headers, test_project, make_contributor):
        """review_count_90d ≥ 5 → reviewer。"""
        make_contributor(test_project, github_handle="reviewer_user", review_count_90d=10)
        resp = client.get("/api/insights/people", headers=auth_headers)
        assert resp.status_code == 200
        person = next(p for p in resp.json() if p["github_handle"] == "reviewer_user")
        assert "reviewer" in person["influence_types"]

    def test_filter_by_type(self, client: TestClient, auth_headers, test_project, make_contributor):
        make_contributor(test_project, github_handle="norm_user", commit_count_90d=5)
        resp = client.get("/api/insights/people?type=maintainer", headers=auth_headers)
        assert resp.status_code == 200
        # norm_user 不是 maintainer，不应在结果中
        handles = [p["github_handle"] for p in resp.json()]
        assert "norm_user" not in handles

    def test_get_person_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/insights/people/no-such-user", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_person_found(self, client: TestClient, auth_headers, test_project, make_contributor):
        make_contributor(test_project, github_handle="findme", commit_count_90d=20)
        resp = client.get("/api/insights/people/findme", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["github_handle"] == "findme"


# ─── Corporate ────────────────────────────────────────────────────────────────


class TestCorporateEndpoints:
    def test_list_corporate_no_company_data(self, client: TestClient, auth_headers, test_project, make_contributor):
        """无 company 字段时返回空列表。"""
        make_contributor(test_project, github_handle="anon", commit_count_90d=10)
        resp = client.get("/api/insights/corporate", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_corporate_with_data(self, client: TestClient, auth_headers, test_project, make_contributor):
        """有 company 字段时正确聚合。"""
        make_contributor(test_project, github_handle="emp1", company="Acme Corp", commit_count_90d=50)
        make_contributor(test_project, github_handle="emp2", company="Acme Corp", commit_count_90d=30)
        resp = client.get("/api/insights/corporate", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        acme = next(c for c in data if c["company"] == "Acme Corp")
        assert acme["total_contributors"] == 2
        assert acme["project_count"] == 1
        assert len(acme["projects"]) == 1

    def test_corporate_min_projects_filter(self, client: TestClient, auth_headers, test_project, make_contributor):
        """min_projects=2 时，只出现在 1 个项目的企业不返回。"""
        make_contributor(test_project, github_handle="single_emp", company="Solo Inc", commit_count_90d=10)
        resp = client.get("/api/insights/corporate?min_projects=2", headers=auth_headers)
        assert resp.status_code == 200
        companies = [c["company"] for c in resp.json()]
        assert "Solo Inc" not in companies

    def test_get_corporate_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/insights/corporate/NoSuchCorp", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_corporate_found(self, client: TestClient, auth_headers, test_project, make_contributor):
        make_contributor(test_project, github_handle="dev1", company="FoundCorp", commit_count_90d=20)
        resp = client.get("/api/insights/corporate/FoundCorp", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["company"] == "FoundCorp"

    def test_corporate_multi_project(
        self, client: TestClient, auth_headers, test_project, test_project2, make_contributor
    ):
        """同一企业跨 2 个项目 → strategic_score 更高，project_count=2。"""
        make_contributor(test_project, github_handle="mp1", company="BigCorp", commit_count_90d=30)
        make_contributor(test_project2, github_handle="mp2", company="BigCorp", commit_count_90d=20)
        resp = client.get("/api/insights/corporate", headers=auth_headers)
        assert resp.status_code == 200
        bigcorp = next(c for c in resp.json() if c["company"] == "BigCorp")
        assert bigcorp["project_count"] == 2
        assert bigcorp["strategic_score"] > 0

    def test_corporate_has_maintainer(
        self, client: TestClient, auth_headers, test_project, make_contributor
    ):
        """企业内有 maintainer → has_maintainer=True。"""
        make_contributor(
            test_project, github_handle="corp_maint", company="EliteCorp",
            commit_count_90d=50, role="maintainer"
        )
        resp = client.get("/api/insights/corporate", headers=auth_headers)
        assert resp.status_code == 200
        corp = next(c for c in resp.json() if c["company"] == "EliteCorp")
        assert corp["has_maintainer"] is True

    def test_corporate_no_active_projects(
        self, client: TestClient, auth_headers, db_session: Session, test_community, test_user
    ):
        """有公司数据的贡献者存在，但所属项目为非活跃 → 返回空列表。"""
        inactive_project = EcosystemProject(
            community_id=test_community.id,
            added_by_id=test_user.id,
            name="inactiveRepo",
            platform="github",
            org_name="testorg",
            repo_name="inactiverepo",
            is_active=False,
        )
        db_session.add(inactive_project)
        db_session.commit()
        db_session.refresh(inactive_project)

        ghost = EcosystemContributor(
            project_id=inactive_project.id,
            github_handle="ghost_dev",
            display_name="ghost_dev",
            company="GhostCorp",
            commit_count_90d=20,
        )
        db_session.add(ghost)
        db_session.commit()

        resp = client.get("/api/insights/corporate", headers=auth_headers)
        assert resp.status_code == 200
        companies = [c["company"] for c in resp.json()]
        assert "GhostCorp" not in companies
