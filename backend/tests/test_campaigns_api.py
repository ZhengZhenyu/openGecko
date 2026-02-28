"""Campaign 运营活动 API 测试"""
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.campaign import Campaign, CampaignContact, CampaignTask
from app.models.committee import Committee, CommitteeMember
from app.models.people import PersonProfile

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def test_person(db_session: Session, test_community):
    person = PersonProfile(
        display_name="测试联系人",
        github_handle="test-contact",
        source="manual",
    )
    db_session.add(person)
    db_session.commit()
    db_session.refresh(person)
    return person


@pytest.fixture
def test_campaign(db_session: Session, test_community, test_user):
    campaign = Campaign(
        community_id=test_community.id,
        owner_ids=[test_user.id],
        name="测试运营活动",
        type="promotion",
        description="测试描述",
        status="active",
    )
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)
    return campaign


@pytest.fixture
def test_contact(db_session: Session, test_campaign, test_person):
    contact = CampaignContact(
        campaign_id=test_campaign.id,
        person_id=test_person.id,
        status="pending",
        added_by="manual",
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)
    return contact


# ─── Campaign CRUD ────────────────────────────────────────────────────────────

class TestListCampaigns:
    def test_list_campaigns_empty(self, client: TestClient, auth_headers):
        resp = client.get("/api/campaigns", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_campaigns_returns_data(self, client: TestClient, auth_headers, test_campaign):
        resp = client.get("/api/campaigns", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "测试运营活动"

    def test_list_campaigns_filter_by_type(self, client: TestClient, auth_headers, test_campaign):
        resp = client.get("/api/campaigns?type=promotion", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        resp2 = client.get("/api/campaigns?type=care", headers=auth_headers)
        assert resp2.status_code == 200
        assert resp2.json() == []

    def test_list_campaigns_filter_by_status(self, client: TestClient, auth_headers, test_campaign):
        resp = client.get("/api/campaigns?status=active", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        resp2 = client.get("/api/campaigns?status=completed", headers=auth_headers)
        assert resp2.status_code == 200
        assert resp2.json() == []


class TestCreateCampaign:
    def test_create_campaign_success(self, client: TestClient, auth_headers):
        resp = client.post("/api/campaigns", headers=auth_headers, json={
            "name": "新活动",
            "type": "care",
            "description": "描述",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "新活动"
        assert data["type"] == "care"
        assert data["status"] == "active"

    def test_create_campaign_invalid_type(self, client: TestClient, auth_headers):
        resp = client.post("/api/campaigns", headers=auth_headers, json={
            "name": "活动",
            "type": "invalid_type",
        })
        assert resp.status_code == 400

    def test_create_campaign_minimal(self, client: TestClient, auth_headers):
        resp = client.post("/api/campaigns", headers=auth_headers, json={
            "name": "最简活动",
            "type": "survey",
        })
        assert resp.status_code == 201


class TestGetCampaign:
    def test_get_campaign_success(self, client: TestClient, auth_headers, test_campaign):
        resp = client.get(f"/api/campaigns/{test_campaign.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "测试运营活动"

    def test_get_campaign_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/campaigns/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_campaign_cross_community_accessible(self, client: TestClient, another_user_auth_headers, test_campaign):
        """运营活动采用 community association 模式，跨社区用户也可访问"""
        resp = client.get(f"/api/campaigns/{test_campaign.id}", headers=another_user_auth_headers)
        assert resp.status_code == 200


class TestUpdateCampaign:
    def test_update_campaign_name(self, client: TestClient, auth_headers, test_campaign):
        resp = client.patch(f"/api/campaigns/{test_campaign.id}", headers=auth_headers, json={
            "name": "新名称",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "新名称"

    def test_update_campaign_status(self, client: TestClient, auth_headers, test_campaign):
        resp = client.patch(f"/api/campaigns/{test_campaign.id}", headers=auth_headers, json={
            "status": "active",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    def test_update_campaign_invalid_status(self, client: TestClient, auth_headers, test_campaign):
        resp = client.patch(f"/api/campaigns/{test_campaign.id}", headers=auth_headers, json={
            "status": "invalid",
        })
        assert resp.status_code == 400

    def test_update_campaign_not_found(self, client: TestClient, auth_headers):
        resp = client.patch("/api/campaigns/99999", headers=auth_headers, json={"name": "x"})
        assert resp.status_code == 404


class TestCampaignFunnel:
    def test_funnel_empty(self, client: TestClient, auth_headers, test_campaign):
        resp = client.get(f"/api/campaigns/{test_campaign.id}/funnel", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["pending"] == 0

    def test_funnel_with_contacts(self, client: TestClient, auth_headers, test_campaign, test_contact):
        resp = client.get(f"/api/campaigns/{test_campaign.id}/funnel", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["pending"] == 1

    def test_funnel_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/campaigns/99999/funnel", headers=auth_headers)
        assert resp.status_code == 404


# ─── Contacts ─────────────────────────────────────────────────────────────────

class TestListContacts:
    def test_list_contacts_empty(self, client: TestClient, auth_headers, test_campaign):
        resp = client.get(f"/api/campaigns/{test_campaign.id}/contacts", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_contacts_with_data(self, client: TestClient, auth_headers, test_campaign, test_contact):
        resp = client.get(f"/api/campaigns/{test_campaign.id}/contacts", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    def test_list_contacts_filter_by_status(self, client: TestClient, auth_headers, test_campaign, test_contact):
        resp = client.get(f"/api/campaigns/{test_campaign.id}/contacts?status=pending", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        resp2 = client.get(f"/api/campaigns/{test_campaign.id}/contacts?status=blocked", headers=auth_headers)
        assert resp2.status_code == 200
        assert resp2.json()["total"] == 0

    def test_list_contacts_campaign_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/campaigns/99999/contacts", headers=auth_headers)
        assert resp.status_code == 404


class TestAddContact:
    def test_add_contact_success(self, client: TestClient, auth_headers, test_campaign, test_person):
        resp = client.post(f"/api/campaigns/{test_campaign.id}/contacts", headers=auth_headers, json={
            "person_id": test_person.id,
            "channel": "email",
            "notes": "测试备注",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["person_id"] == test_person.id
        assert data["status"] == "pending"

    def test_add_contact_duplicate(self, client: TestClient, auth_headers, test_campaign, test_contact, test_person):
        resp = client.post(f"/api/campaigns/{test_campaign.id}/contacts", headers=auth_headers, json={
            "person_id": test_person.id,
        })
        assert resp.status_code == 400

    def test_add_contact_campaign_not_found(self, client: TestClient, auth_headers, test_person):
        resp = client.post("/api/campaigns/99999/contacts", headers=auth_headers, json={
            "person_id": test_person.id,
        })
        assert resp.status_code == 404


class TestUpdateContactStatus:
    def test_update_status_success(self, client: TestClient, auth_headers, test_campaign, test_contact):
        resp = client.patch(
            f"/api/campaigns/{test_campaign.id}/contacts/{test_contact.id}/status",
            headers=auth_headers,
            json={"status": "contacted", "channel": "wechat"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "contacted"

    def test_update_status_invalid(self, client: TestClient, auth_headers, test_campaign, test_contact):
        resp = client.patch(
            f"/api/campaigns/{test_campaign.id}/contacts/{test_contact.id}/status",
            headers=auth_headers,
            json={"status": "invalid_status"},
        )
        assert resp.status_code == 400

    def test_update_status_not_found(self, client: TestClient, auth_headers, test_campaign):
        resp = client.patch(
            f"/api/campaigns/{test_campaign.id}/contacts/99999/status",
            headers=auth_headers,
            json={"status": "contacted"},
        )
        assert resp.status_code == 404


# ─── Bulk Import ──────────────────────────────────────────────────────────────

class TestImportFromPeople:
    def test_import_from_people_success(self, client: TestClient, auth_headers, test_campaign, test_person):
        resp = client.post(
            f"/api/campaigns/{test_campaign.id}/contacts/import-people",
            headers=auth_headers,
            json={"person_ids": [test_person.id]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 1
        assert data["skipped"] == 0

    def test_import_from_people_skips_duplicate(self, client: TestClient, auth_headers, test_campaign, test_contact, test_person):
        resp = client.post(
            f"/api/campaigns/{test_campaign.id}/contacts/import-people",
            headers=auth_headers,
            json={"person_ids": [test_person.id]},
        )
        assert resp.status_code == 200
        assert resp.json()["skipped"] == 1

    def test_import_from_people_invalid_ids(self, client: TestClient, auth_headers, test_campaign):
        resp = client.post(
            f"/api/campaigns/{test_campaign.id}/contacts/import-people",
            headers=auth_headers,
            json={"person_ids": [99999]},
        )
        assert resp.status_code == 400

    def test_import_from_people_campaign_not_found(self, client: TestClient, auth_headers, test_person):
        resp = client.post(
            "/api/campaigns/99999/contacts/import-people",
            headers=auth_headers,
            json={"person_ids": [test_person.id]},
        )
        assert resp.status_code == 404


# ─── Activities ───────────────────────────────────────────────────────────────

class TestActivities:
    def test_list_activities_empty(self, client: TestClient, auth_headers, test_campaign, test_contact):
        resp = client.get(
            f"/api/campaigns/{test_campaign.id}/contacts/{test_contact.id}/activities",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_activities_contact_not_found(self, client: TestClient, auth_headers, test_campaign):
        resp = client.get(
            f"/api/campaigns/{test_campaign.id}/contacts/99999/activities",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_add_activity_success(self, client: TestClient, auth_headers, test_campaign, test_contact):
        resp = client.post(
            f"/api/campaigns/{test_campaign.id}/contacts/{test_contact.id}/activities",
            headers=auth_headers,
            json={"action": "email_sent", "content": "发送邀请邮件", "outcome": "已读"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["action"] == "email_sent"

    def test_add_activity_contact_not_found(self, client: TestClient, auth_headers, test_campaign):
        resp = client.post(
            f"/api/campaigns/{test_campaign.id}/contacts/99999/activities",
            headers=auth_headers,
            json={"action": "call"},
        )
        assert resp.status_code == 404


# ─── New campaign types ────────────────────────────────────────────────────────

class TestNewCampaignTypes:
    """新版三种活动类型能够正常创建与过滤。"""

    @pytest.mark.parametrize("campaign_type", ["default", "community_care", "developer_care"])
    def test_create_new_type(self, client: TestClient, auth_headers, campaign_type):
        resp = client.post("/api/campaigns", headers=auth_headers, json={
            "name": f"新类型活动-{campaign_type}",
            "type": campaign_type,
        })
        assert resp.status_code == 201
        assert resp.json()["type"] == campaign_type

    @pytest.mark.parametrize("campaign_type", ["default", "community_care", "developer_care"])
    def test_filter_by_new_type(self, client: TestClient, auth_headers, campaign_type):
        # 先创建
        client.post("/api/campaigns", headers=auth_headers, json={
            "name": f"过滤活动-{campaign_type}",
            "type": campaign_type,
        })
        resp = client.get(f"/api/campaigns?type={campaign_type}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(c["type"] == campaign_type for c in data)

    def test_create_default_with_owner(self, client: TestClient, auth_headers):
        """指定 owner_ids 应被接受（后端以请求值为准）。"""
        resp = client.post("/api/campaigns", headers=auth_headers, json={
            "name": "指定owner活动",
            "type": "default",
            "owner_ids": [1],
        })
        assert resp.status_code == 201


# ─── Available Committees ──────────────────────────────────────────────────────

@pytest.fixture
def test_committee(db_session: Session, test_community):
    committee = Committee(
        community_id=test_community.id,
        name="测试委员会",
        slug="test-committee",
        is_active=True,
    )
    db_session.add(committee)
    db_session.commit()
    db_session.refresh(committee)
    return committee


@pytest.fixture
def test_community_care_campaign(db_session: Session, test_community, test_user):
    campaign = Campaign(
        community_id=test_community.id,
        owner_ids=[test_user.id],
        name="社区成员关怀活动",
        type="community_care",
        status="active",
    )
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)
    return campaign


@pytest.fixture
def test_campaign_no_community(db_session: Session, test_user):
    campaign = Campaign(
        community_id=None,
        owner_ids=[test_user.id],
        name="无社区活动",
        type="default",
        status="active",
    )
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)
    return campaign


class TestAvailableCommittees:
    def test_list_committees_empty(self, client: TestClient, auth_headers, test_community_care_campaign):
        """社区存在但无委员会时，返回空列表。"""
        resp = client.get(
            f"/api/campaigns/{test_community_care_campaign.id}/available-committees",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_committees_with_data(
        self, client: TestClient, auth_headers, test_community_care_campaign, test_committee
    ):
        resp = client.get(
            f"/api/campaigns/{test_community_care_campaign.id}/available-committees",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "测试委员会"
        assert "member_count" in data[0]

    def test_list_committees_campaign_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/campaigns/99999/available-committees", headers=auth_headers)
        assert resp.status_code == 404

    def test_list_committees_no_community(
        self, client: TestClient, auth_headers, test_campaign_no_community
    ):
        """活动未关联社区时，返回 400。"""
        resp = client.get(
            f"/api/campaigns/{test_campaign_no_community.id}/available-committees",
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_inactive_committee_excluded(
        self, client: TestClient, auth_headers, test_community_care_campaign, db_session, test_community
    ):
        """is_active=False 的委员会不应出现在列表中。"""
        inactive = Committee(
            community_id=test_community.id,
            name="非激活委员会",
            slug="inactive-committee",
            is_active=False,
        )
        db_session.add(inactive)
        db_session.commit()
        resp = client.get(
            f"/api/campaigns/{test_community_care_campaign.id}/available-committees",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "非激活委员会" not in names


# ─── Import from Committees ────────────────────────────────────────────────────

@pytest.fixture
def test_member_with_person(db_session: Session, test_committee, test_person):
    """已有 PersonProfile 的委员会成员。"""
    member = CommitteeMember(
        committee_id=test_committee.id,
        name=test_person.display_name,
        email="test@example.com",
        person_id=test_person.id,
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    return member


@pytest.fixture
def test_member_no_person(db_session: Session, test_committee):
    """没有关联 PersonProfile 的委员会成员（应自动创建档案）。"""
    member = CommitteeMember(
        committee_id=test_committee.id,
        name="无档案委员",
        email="no-profile@example.com",
        person_id=None,
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    return member


class TestImportFromCommittees:
    def test_import_member_with_person(
        self, client, auth_headers, test_community_care_campaign, test_committee, test_member_with_person
    ):
        resp = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-committee",
            headers=auth_headers,
            json={"committee_ids": [test_committee.id]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 1
        assert data["skipped"] == 0

    def test_import_member_auto_creates_profile(
        self, client, auth_headers, test_community_care_campaign, test_committee,
        test_member_no_person, db_session
    ):
        """无 PersonProfile 的成员应自动创建档案后导入。"""
        resp = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-committee",
            headers=auth_headers,
            json={"committee_ids": [test_committee.id]},
        )
        assert resp.status_code == 200
        assert resp.json()["created"] == 1
        # 验证 PersonProfile 已被创建
        person = db_session.query(PersonProfile).filter(
            PersonProfile.email == "no-profile@example.com"
        ).first()
        assert person is not None
        assert person.display_name == "无档案委员"

    def test_import_dedup_within_campaign(
        self, client, auth_headers, test_community_care_campaign, test_committee,
        test_member_with_person, db_session
    ):
        """已在此 community_care campaign 中的联系人应被跳过（skipped）。"""
        # 先手动把同一个 person 加入 community_care campaign
        db_session.add(CampaignContact(
            campaign_id=test_community_care_campaign.id,
            person_id=test_member_with_person.person_id,
            added_by="manual",
        ))
        db_session.commit()

        resp = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-committee",
            headers=auth_headers,
            json={"committee_ids": [test_committee.id]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 0
        assert data["skipped"] >= 1

    def test_import_committee_not_in_community(
        self, client, auth_headers, test_community_care_campaign, db_session
    ):
        """属于其他社区的委员会应返回 400。"""
        other = Committee(
            community_id=9999,  # 不存在的社区
            name="外部委员会",
            slug="external",
            is_active=True,
        )
        db_session.add(other)
        db_session.commit()
        resp = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-committee",
            headers=auth_headers,
            json={"committee_ids": [other.id]},
        )
        assert resp.status_code == 400

    def test_import_empty_committee_ids(
        self, client, auth_headers, test_community_care_campaign
    ):
        """空列表时应返回 created=0, skipped=0 而非报错。"""
        resp = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-committee",
            headers=auth_headers,
            json={"committee_ids": []},
        )
        assert resp.status_code == 200
        assert resp.json() == {"created": 0, "skipped": 0}

    def test_import_campaign_not_found(self, client, auth_headers):
        resp = client.post(
            "/api/campaigns/99999/contacts/import-committee",
            headers=auth_headers,
            json={"committee_ids": [1]},
        )
        assert resp.status_code == 404


# ─── Import from CSV ───────────────────────────────────────────────────────────

def _make_csv(rows: list[dict], extra_fields: list[str] | None = None) -> bytes:
    """构造 CSV bytes，首行为 header。"""
    fields = ["display_name", "email", "phone", "company", "github_handle", "notes"]
    if extra_fields:
        fields.extend(extra_fields)
    lines = [",".join(fields)]
    for row in rows:
        lines.append(",".join(str(row.get(f, "")) for f in fields))
    return "\n".join(lines).encode("utf-8")


class TestImportFromCsv:
    def test_import_csv_creates_new_person(
        self, client, auth_headers, test_community_care_campaign
    ):
        csv_bytes = _make_csv([
            {"display_name": "CSV新人员", "email": "csv-new@example.com"},
        ])
        resp = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-csv",
            headers=auth_headers,
            files={"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 1
        assert data["matched"] == 0
        assert data["skipped"] == 0
        assert data["errors"] == []

    def test_import_csv_matches_existing_person(
        self, client, auth_headers, test_community_care_campaign, test_person
    ):
        """email 匹配已有 PersonProfile 时 matched += 1，不重复创建。"""
        # test_person 没有 email，先给它一个  — 直接创建有 email 的人
        csv_bytes = _make_csv([
            {"display_name": "已有人员", "email": "test@example.com"},
        ])
        # 先创建有该 email 的 PersonProfile
        # 直接上传 CSV 第一次 → created=1
        resp1 = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-csv",
            headers=auth_headers,
            files={"file": ("t.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp1.status_code == 200
        # 第二次上传同 email → matched=1, skipped=1（已在 campaign）
        csv_bytes2 = _make_csv([
            {"display_name": "已有人员", "email": "test@example.com"},
        ])
        resp2 = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-csv",
            headers=auth_headers,
            files={"file": ("t2.csv", io.BytesIO(csv_bytes2), "text/csv")},
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["matched"] == 1
        assert data2["skipped"] == 1

    def test_import_csv_skips_existing_contact(
        self, client, auth_headers, test_community_care_campaign, test_person, db_session
    ):
        """已在 campaign 中的人员（通过 person_id 匹配）应被跳过。"""
        from app.models.campaign import CampaignContact
        # 给 test_person 设置 email 以便 CSV 能匹配
        test_person.email = "skip-test@example.com"
        db_session.commit()

        # 先手动加入 campaign
        db_session.add(CampaignContact(
            campaign_id=test_community_care_campaign.id,
            person_id=test_person.id,
            added_by="manual",
        ))
        db_session.commit()

        csv_bytes = _make_csv([
            {"display_name": test_person.display_name, "email": "skip-test@example.com"},
        ])
        resp = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-csv",
            headers=auth_headers,
            files={"file": ("t.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["skipped"] == 1

    def test_import_csv_empty_name_is_error(
        self, client, auth_headers, test_community_care_campaign
    ):
        """display_name 为空的行应记入 errors 而不是抛 500。"""
        csv_bytes = _make_csv([
            {"display_name": "", "email": "noemail@example.com"},
        ])
        resp = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-csv",
            headers=auth_headers,
            files={"file": ("t.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["errors"]) >= 1
        assert data["created"] == 0

    def test_import_csv_missing_display_name_column(
        self, client, auth_headers, test_community_care_campaign
    ):
        """缺少 display_name 列时返回 400。"""
        csv_bytes = b"email,phone\njohn@example.com,1234\n"
        resp = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-csv",
            headers=auth_headers,
            files={"file": ("bad.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 400

    def test_import_csv_bom_utf8(
        self, client, auth_headers, test_community_care_campaign
    ):
        """支持 Excel 导出的 UTF-8 BOM 编码。"""
        content = "display_name,email\nBOM用户,bom@example.com\n"
        csv_bytes = ("\ufeff" + content).encode("utf-8")
        resp = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-csv",
            headers=auth_headers,
            files={"file": ("bom.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 200
        assert resp.json()["created"] == 1

    def test_import_csv_multiple_rows(
        self, client, auth_headers, test_community_care_campaign
    ):
        """多行正常导入。"""
        rows = [
            {"display_name": f"用户{i}", "email": f"user{i}@example.com"}
            for i in range(5)
        ]
        csv_bytes = _make_csv(rows)
        resp = client.post(
            f"/api/campaigns/{test_community_care_campaign.id}/contacts/import-csv",
            headers=auth_headers,
            files={"file": ("multi.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 5
        assert data["errors"] == []

    def test_import_csv_campaign_not_found(self, client, auth_headers):
        csv_bytes = _make_csv([{"display_name": "人员", "email": "x@y.com"}])
        resp = client.post(
            "/api/campaigns/99999/contacts/import-csv",
            headers=auth_headers,
            files={"file": ("t.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 404


# ─── Campaign Task CRUD ───────────────────────────────────────────────────────

class TestCampaignTasks:
    def test_list_tasks_empty(self, client: TestClient, auth_headers, test_campaign):
        resp = client.get(f"/api/campaigns/{test_campaign.id}/tasks", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_task(self, client: TestClient, auth_headers, test_campaign, test_user):
        resp = client.post(
            f"/api/campaigns/{test_campaign.id}/tasks",
            headers=auth_headers,
            json={
                "title": "发布公告",
                "description": "在官网发布公告",
                "priority": "high",
                "assignee_ids": [test_user.id],
                "deadline": "2099-12-31",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "发布公告"
        assert data["priority"] == "high"
        assert data["status"] == "not_started"
        assert test_user.id in data["assignee_ids"]
        assert data["deadline"] == "2099-12-31"

    def test_update_task(self, client: TestClient, auth_headers, test_campaign, db_session: Session):
        task = CampaignTask(
            campaign_id=test_campaign.id,
            title="待更新任务",
            status="not_started",
            priority="low",
            assignee_ids=[],
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        resp = client.patch(
            f"/api/campaigns/{test_campaign.id}/tasks/{task.id}",
            headers=auth_headers,
            json={"status": "in_progress", "title": "已更新任务"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "in_progress"
        assert data["title"] == "已更新任务"

    def test_delete_task(self, client: TestClient, auth_headers, test_campaign, db_session: Session):
        task = CampaignTask(
            campaign_id=test_campaign.id,
            title="待删除任务",
            status="not_started",
            priority="medium",
            assignee_ids=[],
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        resp = client.delete(
            f"/api/campaigns/{test_campaign.id}/tasks/{task.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

        # 验证已删除
        resp2 = client.get(f"/api/campaigns/{test_campaign.id}/tasks", headers=auth_headers)
        ids = [t["id"] for t in resp2.json()]
        assert task.id not in ids

    def test_task_not_found(self, client: TestClient, auth_headers, test_campaign):
        resp = client.patch(
            f"/api/campaigns/{test_campaign.id}/tasks/99999",
            headers=auth_headers,
            json={"title": "不存在"},
        )
        assert resp.status_code == 404

    def test_create_task_campaign_not_found(self, client: TestClient, auth_headers):
        resp = client.post(
            "/api/campaigns/99999/tasks",
            headers=auth_headers,
            json={"title": "不存在的活动", "priority": "low"},
        )
        assert resp.status_code == 404

    def test_list_tasks_campaign_not_found(self, client: TestClient, auth_headers):
        """GET /{cid}/tasks 当活动不存在时返回 404（覆盖 line 583）"""
        resp = client.get("/api/campaigns/99999/tasks", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_task_not_found(
        self, client: TestClient, auth_headers, test_campaign
    ):
        """DELETE /{cid}/tasks/{tid} 当任务不存在时返回 404（覆盖 line 648）"""
        resp = client.delete(
            f"/api/campaigns/{test_campaign.id}/tasks/99999",
            headers=auth_headers,
        )
        assert resp.status_code == 404


# ─── Bulk Status Update ──────────────────────────────────────────────────────────────────

class TestBulkUpdateContactStatus:
    def test_bulk_update_success(
        self, client: TestClient, auth_headers, test_campaign, test_contact
    ):
        """PATCH /{cid}/contacts/bulk-status 成功批量更新"""
        resp = client.patch(
            f"/api/campaigns/{test_campaign.id}/contacts/bulk-status",
            headers=auth_headers,
            json={"contact_ids": [test_contact.id], "status": "contacted"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["updated"] == 1
        # 验证状态确实已变更
        check = client.get(
            f"/api/campaigns/{test_campaign.id}/contacts/{test_contact.id}",
            headers=auth_headers,
        )
        if check.status_code == 200:
            assert check.json()["status"] == "contacted"

    def test_bulk_update_invalid_status(
        self, client: TestClient, auth_headers, test_campaign, test_contact
    ):
        """PATCH /{cid}/contacts/bulk-status 无效状态返回 400"""
        resp = client.patch(
            f"/api/campaigns/{test_campaign.id}/contacts/bulk-status",
            headers=auth_headers,
            json={"contact_ids": [test_contact.id], "status": "invalid_status"},
        )
        assert resp.status_code == 400

    def test_bulk_update_campaign_not_found(
        self, client: TestClient, auth_headers, test_contact
    ):
        """PATCH /{cid}/contacts/bulk-status 当活动不存在时返回 404"""
        resp = client.patch(
            "/api/campaigns/99999/contacts/bulk-status",
            headers=auth_headers,
            json={"contact_ids": [test_contact.id], "status": "blocked"},
        )
        assert resp.status_code == 404

    def test_bulk_update_empty_ids(
        self, client: TestClient, auth_headers, test_campaign
    ):
        """空列表返回 updated=0"""
        resp = client.patch(
            f"/api/campaigns/{test_campaign.id}/contacts/bulk-status",
            headers=auth_headers,
            json={"contact_ids": [], "status": "pending"},
        )
        assert resp.status_code == 200
        assert resp.json()["updated"] == 0


# ─── Delete Campaign ──────────────────────────────────────────────────────────────────────────────

class TestDeleteCampaign:
    def test_delete_campaign_success(
        self, client: TestClient, auth_headers, test_campaign
    ):
        """删除活动成功返回 204"""
        resp = client.delete(f"/api/campaigns/{test_campaign.id}", headers=auth_headers)
        assert resp.status_code == 204
        # 确认已删除
        get_resp = client.get(f"/api/campaigns/{test_campaign.id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_campaign_not_found(
        self, client: TestClient, auth_headers
    ):
        """删除不存在的活动返回 404"""
        resp = client.delete("/api/campaigns/99999", headers=auth_headers)
        assert resp.status_code == 404