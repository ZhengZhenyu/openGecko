"""
Tests for governance module API endpoints (committees + members).

Endpoints tested:
- GET /api/committees
- POST /api/committees
- GET /api/committees/{id}
- PUT /api/committees/{id}
- DELETE /api/committees/{id}
- GET /api/committees/{id}/members
- POST /api/committees/{id}/members
- GET /api/committees/{id}/members/{mid}
- PUT /api/committees/{id}/members/{mid}
- DELETE /api/committees/{id}/members/{mid}
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.user import User
from app.models.committee import Committee, CommitteeMember


# ==================== Fixtures ====================

def _create_committee(db_session: Session, community_id: int, **kwargs) -> Committee:
    defaults = {
        "name": "技术委员会",
        "slug": "tech-committee",
        "description": "负责技术方向决策",
        "is_active": True,
    }
    defaults.update(kwargs)
    committee = Committee(community_id=community_id, **defaults)
    db_session.add(committee)
    db_session.commit()
    db_session.refresh(committee)
    return committee


def _create_member(db_session: Session, committee_id: int, **kwargs) -> CommitteeMember:
    defaults = {
        "name": "张三",
        "email": "zhangsan@example.com",
        "roles": ["主席"],
    }
    defaults.update(kwargs)
    member = CommitteeMember(committee_id=committee_id, **defaults)
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    return member


# ==================== Committee CRUD Tests ====================

class TestListCommittees:

    def test_list_empty(
        self, client: TestClient, auth_headers: dict
    ):
        response = client.get("/api/committees", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_with_data(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        _create_committee(db_session, test_community.id)
        _create_committee(
            db_session, test_community.id,
            name="市场委员会", slug="marketing-committee",
        )

        response = client.get("/api/committees", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_filter_active(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        _create_committee(db_session, test_community.id)
        _create_committee(
            db_session, test_community.id,
            name="已停用委员会", slug="inactive", is_active=False,
        )

        response = client.get(
            "/api/committees?is_active=true", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "技术委员会"

    def test_list_community_isolation(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_another_community: Community,
        auth_headers: dict,
    ):
        """委员会只能看到当前社区的。"""
        _create_committee(db_session, test_community.id)
        _create_committee(
            db_session, test_another_community.id,
            name="其他社区委员会", slug="other",
        )

        response = client.get("/api/committees", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "技术委员会"

    def test_list_no_auth(self, client: TestClient):
        response = client.get("/api/committees")
        assert response.status_code == 401


class TestCreateCommittee:

    def test_create_success(
        self, client: TestClient, auth_headers: dict
    ):
        response = client.post(
            "/api/committees",
            headers=auth_headers,
            json={
                "name": "技术委员会",
                "slug": "tech-committee",
                "description": "负责技术方向决策",
                "meeting_frequency": "monthly",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "技术委员会"
        assert data["slug"] == "tech-committee"
        assert data["meeting_frequency"] == "monthly"
        assert data["member_count"] == 0
        assert data["is_active"] is True

    def test_create_duplicate_slug(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        _create_committee(db_session, test_community.id)

        response = client.post(
            "/api/committees",
            headers=auth_headers,
            json={"name": "另一个委员会", "slug": "tech-committee"},
        )
        assert response.status_code == 409

    def test_create_invalid_slug(
        self, client: TestClient, auth_headers: dict
    ):
        response = client.post(
            "/api/committees",
            headers=auth_headers,
            json={"name": "测试", "slug": "Invalid Slug!"},
        )
        assert response.status_code == 422


class TestGetCommittee:

    def test_get_with_members(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        _create_member(db_session, committee.id)

        response = client.get(
            f"/api/committees/{committee.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "技术委员会"
        assert data["member_count"] == 1
        assert len(data["members"]) == 1
        assert data["members"][0]["name"] == "张三"

    def test_get_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        response = client.get("/api/committees/9999", headers=auth_headers)
        assert response.status_code == 404


class TestUpdateCommittee:

    def test_update_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)

        response = client.put(
            f"/api/committees/{committee.id}",
            headers=auth_headers,
            json={"name": "技术与架构委员会", "meeting_frequency": "quarterly"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "技术与架构委员会"
        assert data["meeting_frequency"] == "quarterly"

    def test_update_partial(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)

        response = client.put(
            f"/api/committees/{committee.id}",
            headers=auth_headers,
            json={"is_active": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["name"] == "技术委员会"  # unchanged


class TestDeleteCommittee:

    def test_delete_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        _create_member(db_session, committee.id)

        response = client.delete(
            f"/api/committees/{committee.id}", headers=auth_headers
        )
        assert response.status_code == 204

        # Verify cascade deletion
        assert db_session.query(Committee).filter(Committee.id == committee.id).first() is None
        assert (
            db_session.query(CommitteeMember)
            .filter(CommitteeMember.committee_id == committee.id)
            .first()
        ) is None

    def test_delete_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        response = client.delete("/api/committees/9999", headers=auth_headers)
        assert response.status_code == 404


# ==================== Member Management Tests ====================

class TestListMembers:

    def test_list_members(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        _create_member(db_session, committee.id)
        _create_member(
            db_session, committee.id,
            name="李四", email="lisi@example.com", roles=["委员"],
        )

        response = client.get(
            f"/api/committees/{committee.id}/members", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_members_filter_role(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        _create_member(db_session, committee.id, name="主席", roles=["主席"])
        _create_member(
            db_session, committee.id,
            name="委员", email="weiyuan@example.com", roles=["委员"],
        )

        response = client.get(
            f"/api/committees/{committee.id}/members?role=主席",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "主席"

    def test_list_members_filter_active(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        _create_member(db_session, committee.id)
        _create_member(
            db_session, committee.id,
            name="已离任", email="old@example.com", is_active=False,
        )

        response = client.get(
            f"/api/committees/{committee.id}/members?is_active=true",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "张三"


class TestAddMember:

    def test_add_member_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)

        response = client.post(
            f"/api/committees/{committee.id}/members",
            headers=auth_headers,
            json={
                "name": "王五",
                "email": "wangwu@example.com",
                "phone": "13800138000",
                "organization": "某科技公司",
                "roles": ["主席", "常务委员"],
                "term_start": "2026-01-01",
                "term_end": "2027-12-31",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "王五"
        assert "主席" in data["roles"]
        assert "常务委员" in data["roles"]
        assert data["organization"] == "某科技公司"
        assert data["is_active"] is True

    def test_add_member_minimal(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)

        response = client.post(
            f"/api/committees/{committee.id}/members",
            headers=auth_headers,
            json={"name": "简单成员"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "简单成员"
        assert data["roles"] == []

    def test_add_member_to_nonexistent_committee(
        self, client: TestClient, auth_headers: dict
    ):
        response = client.post(
            "/api/committees/9999/members",
            headers=auth_headers,
            json={"name": "测试"},
        )
        assert response.status_code == 404


class TestGetMember:

    def test_get_member_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        member = _create_member(db_session, committee.id)

        response = client.get(
            f"/api/committees/{committee.id}/members/{member.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "张三"
        assert data["email"] == "zhangsan@example.com"

    def test_get_member_not_found(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)

        response = client.get(
            f"/api/committees/{committee.id}/members/9999",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestUpdateMember:

    def test_update_member_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        member = _create_member(db_session, committee.id)

        response = client.put(
            f"/api/committees/{committee.id}/members/{member.id}",
            headers=auth_headers,
            json={
                "roles": ["主席", "常务委员"],
                "organization": "新公司",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "主席" in data["roles"]
        assert "常务委员" in data["roles"]
        assert data["organization"] == "新公司"
        assert data["name"] == "张三"  # unchanged

    def test_update_member_deactivate(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        member = _create_member(db_session, committee.id)

        response = client.put(
            f"/api/committees/{committee.id}/members/{member.id}",
            headers=auth_headers,
            json={"is_active": False},
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_update_member_not_found(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)

        response = client.put(
            f"/api/committees/{committee.id}/members/9999",
            headers=auth_headers,
            json={"name": "不存在"},
        )
        assert response.status_code == 404


class TestRemoveMember:

    def test_remove_member_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        member = _create_member(db_session, committee.id)

        response = client.delete(
            f"/api/committees/{committee.id}/members/{member.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify deletion
        assert (
            db_session.query(CommitteeMember)
            .filter(CommitteeMember.id == member.id)
            .first()
        ) is None

    def test_remove_member_not_found(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)

        response = client.delete(
            f"/api/committees/{committee.id}/members/9999",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ==================== member_count Tests ====================

class TestMemberCount:

    def test_member_count_in_list(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        _create_member(db_session, committee.id)
        _create_member(
            db_session, committee.id,
            name="李四", email="lisi@example.com", roles=["委员"],
        )

        response = client.get("/api/committees", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data[0]["member_count"] == 2

    def test_member_count_after_delete(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        member = _create_member(db_session, committee.id)
        _create_member(
            db_session, committee.id,
            name="李四", email="lisi@example.com",
        )

        # Delete one member
        client.delete(
            f"/api/committees/{committee.id}/members/{member.id}",
            headers=auth_headers,
        )

        response = client.get(
            f"/api/committees/{committee.id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["member_count"] == 1
