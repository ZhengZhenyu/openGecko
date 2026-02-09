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


# ==================== CSV Import/Export Tests ====================

class TestCommitteeCSVExport:
    """Test CSV export functionality."""

    def test_export_members_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        _create_member(
            db_session,
            committee.id,
            name="张三",
            email="zhangsan@example.com",
            phone="13800138000",
            wechat="zhangsan_wx",
            organization="测试公司",
            roles=["主席", "秘书"],
            term_start="2024-01-01",
            term_end="2025-12-31",
            is_active=True,
            bio="测试成员简介",
        )
        _create_member(
            db_session,
            committee.id,
            name="李四",
            email="lisi@example.com",
            roles=["成员"],
        )

        response = client.get(
            f"/api/committees/{committee.id}/members/export",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers.get("content-disposition", "")

        # Check CSV content
        csv_content = response.text
        lines = csv_content.strip().split("\n")
        assert len(lines) == 3  # header + 2 members

        # Check header
        header = lines[0]
        assert "name" in header
        assert "email" in header
        assert "roles" in header

        # Check first member data
        assert "张三" in lines[1]
        assert "zhangsan@example.com" in lines[1]
        assert "13800138000" in lines[1]
        assert "测试公司" in lines[1]

    def test_export_empty_committee(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)

        response = client.get(
            f"/api/committees/{committee.id}/members/export",
            headers=auth_headers,
        )

        assert response.status_code == 200
        csv_content = response.text
        lines = csv_content.strip().split("\n")
        assert len(lines) == 1  # only header

    def test_export_nonexistent_committee(
        self, client: TestClient, auth_headers: dict
    ):
        response = client.get(
            "/api/committees/99999/members/export",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestCommitteeCSVImport:
    """Test CSV import functionality."""

    def test_import_members_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
        tmp_path,
    ):
        committee = _create_committee(db_session, test_community.id)

        # Create CSV file
        csv_content = """name,email,phone,wechat,organization,roles,term_start,term_end,is_active,bio
张三,zhangsan@example.com,13800138000,zhangsan_wx,测试公司,"主席,秘书",2024-01-01,2025-12-31,true,测试成员
李四,lisi@example.com,13900139000,,另一家公司,成员,2024-01-01,,true,
王五,wangwu@example.com,,,,观察员,2024-01-01,2024-12-31,false,临时成员"""

        csv_file = tmp_path / "members.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        with open(csv_file, "rb") as f:
            response = client.post(
                f"/api/committees/{committee.id}/members/import",
                headers=auth_headers,
                files={"file": ("members.csv", f, "text/csv")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
        assert data["error_count"] == 0
        assert len(data["errors"]) == 0

        # Verify members were created
        members = db_session.query(CommitteeMember).filter_by(
            committee_id=committee.id
        ).all()
        assert len(members) == 3

        # Check first member
        zhang = next(m for m in members if m.name == "张三")
        assert zhang.email == "zhangsan@example.com"
        assert zhang.phone == "13800138000"
        assert zhang.wechat == "zhangsan_wx"
        assert zhang.organization == "测试公司"
        assert "主席" in zhang.roles
        assert "秘书" in zhang.roles
        assert zhang.is_active is True

    def test_import_invalid_file_type(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
        tmp_path,
    ):
        committee = _create_committee(db_session, test_community.id)

        # Create non-CSV file
        txt_file = tmp_path / "members.txt"
        txt_file.write_text("not a csv")

        with open(txt_file, "rb") as f:
            response = client.post(
                f"/api/committees/{committee.id}/members/import",
                headers=auth_headers,
                files={"file": ("members.txt", f, "text/plain")},
            )

        assert response.status_code == 400
        assert "Only CSV files" in response.json()["detail"]

    def test_import_missing_required_field(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
        tmp_path,
    ):
        committee = _create_committee(db_session, test_community.id)

        # CSV without name field
        csv_content = """email,phone,organization
test@example.com,13800138000,测试公司"""

        csv_file = tmp_path / "members.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        with open(csv_file, "rb") as f:
            response = client.post(
                f"/api/committees/{committee.id}/members/import",
                headers=auth_headers,
                files={"file": ("members.csv", f, "text/csv")},
            )

        assert response.status_code == 400
        assert "name" in response.json()["detail"].lower()

    def test_import_invalid_date_format(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
        tmp_path,
    ):
        committee = _create_committee(db_session, test_community.id)

        csv_content = """name,email,term_start
张三,zhangsan@example.com,2024/01/01"""

        csv_file = tmp_path / "members.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        with open(csv_file, "rb") as f:
            response = client.post(
                f"/api/committees/{committee.id}/members/import",
                headers=auth_headers,
                files={"file": ("members.csv", f, "text/csv")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 0
        assert data["error_count"] == 1
        assert len(data["errors"]) > 0
        assert "Row 2" in data["errors"][0]

    def test_import_duplicate_names(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
        tmp_path,
    ):
        committee = _create_committee(db_session, test_community.id)

        # Pre-existing member
        _create_member(db_session, committee.id, name="张三")

        csv_content = """name,email
张三,zhangsan@example.com
李四,lisi@example.com"""

        csv_file = tmp_path / "members.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        with open(csv_file, "rb") as f:
            response = client.post(
                f"/api/committees/{committee.id}/members/import",
                headers=auth_headers,
                files={"file": ("members.csv", f, "text/csv")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
        assert data["error_count"] == 1
        assert any("already exists" in err for err in data["errors"])

    def test_import_partial_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
        tmp_path,
    ):
        committee = _create_committee(db_session, test_community.id)

        # Mix of valid and invalid rows
        csv_content = """name,email,term_start
张三,zhangsan@example.com,2024-01-01
,lisi@example.com,2024-01-01
王五,wangwu@example.com,invalid-date"""

        csv_file = tmp_path / "members.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        with open(csv_file, "rb") as f:
            response = client.post(
                f"/api/committees/{committee.id}/members/import",
                headers=auth_headers,
                files={"file": ("members.csv", f, "text/csv")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1  # Only 张三 succeeded
        assert data["error_count"] == 2
        assert len(data["errors"]) == 2

    def test_import_utf8_bom(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
        tmp_path,
    ):
        """Test that UTF-8 BOM is handled correctly (Excel compatibility)."""
        committee = _create_committee(db_session, test_community.id)

        csv_content = """name,email
张三,zhangsan@example.com"""

        csv_file = tmp_path / "members_bom.csv"
        # Write with BOM
        csv_file.write_bytes(b"\xef\xbb\xbf" + csv_content.encode("utf-8"))

        with open(csv_file, "rb") as f:
            response = client.post(
                f"/api/committees/{committee.id}/members/import",
                headers=auth_headers,
                files={"file": ("members.csv", f, "text/csv")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
        assert data["error_count"] == 0

    def test_import_nonexistent_committee(
        self, client: TestClient, auth_headers: dict, tmp_path
    ):
        csv_content = """name,email
张三,zhangsan@example.com"""

        csv_file = tmp_path / "members.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        with open(csv_file, "rb") as f:
            response = client.post(
                "/api/committees/99999/members/import",
                headers=auth_headers,
                files={"file": ("members.csv", f, "text/csv")},
            )

        assert response.status_code == 404
