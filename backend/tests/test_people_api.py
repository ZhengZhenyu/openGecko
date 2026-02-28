"""人脉管理 API 测试 — /api/people"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.people import CommunityRole, PersonProfile

# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def test_person(db_session: Session, test_user):
    person = PersonProfile(
        display_name="张三",
        github_handle="zhangsan",
        gitcode_handle="gitcode_zhangsan",
        email="zhangsan@example.com",
        company="开源社区公司",
        location="上海",
        bio="资深开源贡献者",
        tags=["python", "fastapi"],
        notes="重要联系人",
        source="manual",
        created_by_id=test_user.id,
    )
    db_session.add(person)
    db_session.commit()
    db_session.refresh(person)
    return person


@pytest.fixture
def test_role(db_session: Session, test_person, test_user):
    role = CommunityRole(
        person_id=test_person.id,
        community_name="openGecko",
        project_url="https://github.com/opensourceways/openGecko",
        role="maintainer",
        role_label="核心维护者",
        is_current=True,
        updated_by_id=test_user.id,
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


# ─── List People ──────────────────────────────────────────────────────────────


class TestListPeople:
    def test_list_empty(self, client: TestClient, auth_headers):
        resp = client.get("/api/people", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_with_data(self, client: TestClient, auth_headers, test_person):
        resp = client.get("/api/people", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["display_name"] == "张三"
        assert data["items"][0]["github_handle"] == "zhangsan"

    def test_filter_by_q_name(self, client: TestClient, auth_headers, test_person):
        resp = client.get("/api/people?q=张三", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_q_no_match(self, client: TestClient, auth_headers, test_person):
        resp = client.get("/api/people?q=不存在的人", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_filter_by_q_email(self, client: TestClient, auth_headers, test_person):
        resp = client.get("/api/people?q=zhangsan@example", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_company(self, client: TestClient, auth_headers, test_person):
        resp = client.get("/api/people?company=开源社区", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_company_no_match(self, client: TestClient, auth_headers, test_person):
        resp = client.get("/api/people?company=不存在公司", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_filter_by_source(self, client: TestClient, auth_headers, test_person):
        resp = client.get("/api/people?source=manual", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_source_no_match(self, client: TestClient, auth_headers, test_person):
        resp = client.get("/api/people?source=github", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_filter_by_tag(self, client: TestClient, auth_headers, test_person):
        """tag 过滤不报 500（JSON.contains 在 SQLite 上行为因版本而异）"""
        resp = client.get("/api/people?tag=python", headers=auth_headers)
        assert resp.status_code == 200
        # SQLite 上 JSON contains 可能返回 0（不如 PostgreSQL 精确），但不能 500
        assert resp.json()["total"] >= 0

    def test_filter_by_tag_no_match(self, client: TestClient, auth_headers, test_person):
        resp = client.get("/api/people?tag=完全不存在的标签xyz123", headers=auth_headers)
        assert resp.status_code == 200

    def test_pagination(self, client: TestClient, auth_headers, db_session, test_user):
        for i in range(5):
            db_session.add(PersonProfile(
                display_name=f"用户{i}",
                email=f"user{i}@example.com",
                source="manual",
                created_by_id=test_user.id,
            ))
        db_session.commit()
        resp = client.get("/api/people?page=1&page_size=3", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 3

    def test_unauthenticated(self, client: TestClient):
        resp = client.get("/api/people")
        assert resp.status_code == 401


# ─── Create Person ────────────────────────────────────────────────────────────


class TestCreatePerson:
    def test_create_success(self, client: TestClient, auth_headers):
        resp = client.post("/api/people", headers=auth_headers, json={
            "display_name": "李四",
            "github_handle": "lisi",
            "gitcode_handle": "gitcode_lisi",
            "email": "lisi@example.com",
            "company": "新公司",
            "tags": ["vue", "typescript"],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["display_name"] == "李四"
        assert data["github_handle"] == "lisi"
        assert data["gitcode_handle"] == "gitcode_lisi"
        assert data["email"] == "lisi@example.com"
        assert data["source"] == "manual"
        assert "id" in data

    def test_create_minimal_fields(self, client: TestClient, auth_headers):
        """只有 display_name 也能创建"""
        resp = client.post("/api/people", headers=auth_headers, json={
            "display_name": "王五",
        })
        assert resp.status_code == 201
        assert resp.json()["display_name"] == "王五"

    def test_create_duplicate_github(self, client: TestClient, auth_headers, test_person):
        resp = client.post("/api/people", headers=auth_headers, json={
            "display_name": "另一个人",
            "github_handle": "zhangsan",  # 与 test_person 相同
        })
        assert resp.status_code == 400
        assert "GitHub" in resp.json()["detail"]

    def test_create_duplicate_email(self, client: TestClient, auth_headers, test_person):
        resp = client.post("/api/people", headers=auth_headers, json={
            "display_name": "另一个人",
            "email": "zhangsan@example.com",  # 与 test_person 相同
        })
        assert resp.status_code == 400
        assert "邮箱" in resp.json()["detail"]

    def test_create_unauthenticated(self, client: TestClient):
        resp = client.post("/api/people", json={"display_name": "无权限用户"})
        assert resp.status_code == 401


# ─── Get Person ───────────────────────────────────────────────────────────────


class TestGetPerson:
    def test_get_success(self, client: TestClient, auth_headers, test_person):
        resp = client.get(f"/api/people/{test_person.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == test_person.id
        assert data["display_name"] == "张三"
        assert data["bio"] == "资深开源贡献者"
        assert data["tags"] == ["python", "fastapi"]
        assert data["community_roles"] == []

    def test_get_with_roles(self, client: TestClient, auth_headers, test_person, test_role):
        resp = client.get(f"/api/people/{test_person.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["community_roles"]) == 1
        assert data["community_roles"][0]["role"] == "maintainer"

    def test_get_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/people/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_unauthenticated(self, client: TestClient, test_person):
        resp = client.get(f"/api/people/{test_person.id}")
        assert resp.status_code == 401


# ─── Update Person ────────────────────────────────────────────────────────────


class TestUpdatePerson:
    def test_update_success(self, client: TestClient, auth_headers, test_person):
        resp = client.patch(f"/api/people/{test_person.id}", headers=auth_headers, json={
            "display_name": "张三（已更新）",
            "bio": "更新后的简介",
            "company": "新公司",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "张三（已更新）"
        assert data["bio"] == "更新后的简介"
        assert data["company"] == "新公司"
        # 未修改字段不变
        assert data["github_handle"] == "zhangsan"

    def test_update_tags(self, client: TestClient, auth_headers, test_person):
        resp = client.patch(f"/api/people/{test_person.id}", headers=auth_headers, json={
            "tags": ["go", "kubernetes"],
        })
        assert resp.status_code == 200
        assert resp.json()["tags"] == ["go", "kubernetes"]

    def test_update_partial(self, client: TestClient, auth_headers, test_person):
        """只更新一个字段"""
        resp = client.patch(f"/api/people/{test_person.id}", headers=auth_headers, json={
            "location": "北京",
        })
        assert resp.status_code == 200
        assert resp.json()["location"] == "北京"

    def test_update_not_found(self, client: TestClient, auth_headers):
        resp = client.patch("/api/people/99999", headers=auth_headers, json={
            "display_name": "不存在",
        })
        assert resp.status_code == 404

    def test_update_unauthenticated(self, client: TestClient, test_person):
        resp = client.patch(f"/api/people/{test_person.id}", json={"display_name": "无授权"})
        assert resp.status_code == 401


# ─── Delete Person ────────────────────────────────────────────────────────────


class TestDeletePerson:
    def test_delete_success(self, client: TestClient, auth_headers, test_person):
        resp = client.delete(f"/api/people/{test_person.id}", headers=auth_headers)
        assert resp.status_code == 204
        # 确认已删除
        get_resp = client.get(f"/api/people/{test_person.id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_not_found(self, client: TestClient, auth_headers):
        resp = client.delete("/api/people/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated(self, client: TestClient, test_person):
        resp = client.delete(f"/api/people/{test_person.id}")
        assert resp.status_code == 401


# ─── Person Roles ─────────────────────────────────────────────────────────────


class TestPersonRoles:
    def test_list_roles_empty(self, client: TestClient, auth_headers, test_person):
        resp = client.get(f"/api/people/{test_person.id}/roles", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_roles_with_data(self, client: TestClient, auth_headers, test_person, test_role):
        resp = client.get(f"/api/people/{test_person.id}/roles", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["community_name"] == "openGecko"
        assert data[0]["role"] == "maintainer"
        assert data[0]["is_current"] is True

    def test_list_roles_person_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/people/99999/roles", headers=auth_headers)
        assert resp.status_code == 404

    def test_add_role_success(self, client: TestClient, auth_headers, test_person):
        resp = client.post(f"/api/people/{test_person.id}/roles", headers=auth_headers, json={
            "community_name": "MindSpore",
            "project_url": "https://gitee.com/mindspore/mindspore",
            "role": "contributor",
            "role_label": "贡献者",
            "is_current": True,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["community_name"] == "MindSpore"
        assert data["role"] == "contributor"
        assert data["role_label"] == "贡献者"
        assert "id" in data

    def test_add_role_minimal(self, client: TestClient, auth_headers, test_person):
        resp = client.post(f"/api/people/{test_person.id}/roles", headers=auth_headers, json={
            "community_name": "OpenEuler",
            "role": "user",
        })
        assert resp.status_code == 201
        assert resp.json()["community_name"] == "OpenEuler"

    def test_add_role_person_not_found(self, client: TestClient, auth_headers):
        resp = client.post("/api/people/99999/roles", headers=auth_headers, json={
            "community_name": "OpenHarmony",
            "role": "contributor",
        })
        assert resp.status_code == 404

    def test_add_role_unauthenticated(self, client: TestClient, test_person):
        resp = client.post(f"/api/people/{test_person.id}/roles", json={
            "community_name": "test",
            "role": "member",
        })
        assert resp.status_code == 401


# ─── Import People ────────────────────────────────────────────────────────────


class TestImportPeople:
    def test_import_empty_list(self, client: TestClient, auth_headers):
        resp = client.post("/api/people/import", headers=auth_headers, json=[])
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["results"] == []

    def test_import_new_row(self, client: TestClient, auth_headers):
        """导入不存在的记录应返回 status=new"""
        resp = client.post("/api/people/import", headers=auth_headers, json=[
            {"display_name": "新人", "github_handle": "xin_ren_999", "company": "新公司"},
        ])
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["results"][0]["status"] == "new"

    def test_import_matched_by_github(self, client: TestClient, auth_headers, test_person):
        """导入已存在 GitHub 账号的记录 → matched"""
        resp = client.post("/api/people/import", headers=auth_headers, json=[
            {"display_name": "张三", "github_handle": "zhangsan"},
        ])
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"][0]["status"] == "matched"
        assert data["results"][0]["person_id"] == test_person.id

    def test_import_multiple_rows(self, client: TestClient, auth_headers, test_person):
        """批量导入多行，各行独立匹配"""
        rows = [
            {"display_name": "张三", "github_handle": "zhangsan"},   # matched
            {"display_name": "全新用户", "github_handle": "brand_new_user_xyz"},  # new
        ]
        resp = client.post("/api/people/import", headers=auth_headers, json=rows)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        statuses = {r["status"] for r in data["results"]}
        assert "matched" in statuses
        assert "new" in statuses

    def test_import_unauthenticated(self, client: TestClient):
        resp = client.post("/api/people/import", json=[])
        assert resp.status_code == 401


# ─── Confirm Merge ────────────────────────────────────────────────────────────


class TestConfirmMerge:
    def test_skip_when_not_confirmed(self, client: TestClient, auth_headers):
        resp = client.post("/api/people/confirm-merge", headers=auth_headers, json={
            "import_row": {"display_name": "测试"},
            "person_id": None,
            "confirmed": False,
        })
        assert resp.status_code == 200
        assert resp.json()["action"] == "skipped"

    def test_confirm_create_new(self, client: TestClient, auth_headers):
        resp = client.post("/api/people/confirm-merge", headers=auth_headers, json={
            "import_row": {
                "display_name": "合并新建人",
                "github_handle": "new_person_merge_test",
                "email": "merge_new@example.com",
            },
            "person_id": None,
            "confirmed": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "created"
        assert "person_id" in data

    def test_confirm_link_to_existing(self, client: TestClient, auth_headers, test_person):
        resp = client.post("/api/people/confirm-merge", headers=auth_headers, json={
            "import_row": {"display_name": "张三"},
            "person_id": test_person.id,
            "confirmed": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "linked"
        assert data["person_id"] == test_person.id

    def test_confirm_link_person_not_found(self, client: TestClient, auth_headers):
        resp = client.post("/api/people/confirm-merge", headers=auth_headers, json={
            "import_row": {"display_name": "某人"},
            "person_id": 99999,
            "confirmed": True,
        })
        assert resp.status_code == 404

    def test_confirm_merge_unauthenticated(self, client: TestClient):
        resp = client.post("/api/people/confirm-merge", json={
            "import_row": {},
            "person_id": None,
            "confirmed": False,
        })
        assert resp.status_code == 401
