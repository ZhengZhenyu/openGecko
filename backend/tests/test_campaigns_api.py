"""Campaign 运营活动 API 测试"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.campaign import Campaign, CampaignContact
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
        owner_id=test_user.id,
        name="测试运营活动",
        type="promotion",
        description="测试描述",
        status="draft",
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
        resp = client.get("/api/campaigns?status=draft", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        resp2 = client.get("/api/campaigns?status=active", headers=auth_headers)
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
        assert data["status"] == "draft"

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

    def test_get_campaign_wrong_community(self, client: TestClient, another_user_auth_headers, test_campaign):
        resp = client.get(f"/api/campaigns/{test_campaign.id}", headers=another_user_auth_headers)
        assert resp.status_code == 404


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

        resp2 = client.get(f"/api/campaigns/{test_campaign.id}/contacts?status=converted", headers=auth_headers)
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
