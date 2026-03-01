"""通知中心 API 测试。

覆盖：
- TestNotificationsApi     — CRUD 基础流程
- TestNotificationPermissions — 用户只能操作自己的通知
- TestTaskAssignmentTrigger  — 创建/更新任务时自动生成通知
"""
import pytest
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType
from app.models.user import User


# ─── helpers ─────────────────────────────────────────────────────────────────

def _make_notif(db: Session, user_id: int, ntype: str = "task_assigned", is_read: bool = False) -> Notification:
    """直接插入一条通知（不走 HTTP），用于测试读取/更新/删除端点。"""
    n = Notification(
        user_id=user_id,
        type=ntype,
        title="测试通知标题",
        body="测试通知正文",
        is_read=is_read,
        resource_type="event_task",
        resource_id=1,
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── TestNotificationsApi ────────────────────────────────────────────────────

class TestNotificationsApi:
    """基础 CRUD 流程。"""

    def test_list_empty(self, client, user_token):
        """初始状态通知列表为空。"""
        r = client.get("/api/notifications", headers=auth(user_token))
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["unread_count"] == 0
        assert data["items"] == []

    def test_unread_count_zero(self, client, user_token):
        """初始未读数为 0。"""
        r = client.get("/api/notifications/unread-count", headers=auth(user_token))
        assert r.status_code == 200
        assert r.json()["count"] == 0

    def test_list_shows_notification(self, client, db_session, test_user, user_token):
        """写入通知后列表返回该条目。"""
        _make_notif(db_session, test_user.id)
        r = client.get("/api/notifications", headers=auth(user_token))
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["unread_count"] == 1
        item = data["items"][0]
        assert item["is_read"] is False
        assert item["title"] == "测试通知标题"

    def test_unread_count_increments(self, client, db_session, test_user, user_token):
        """写入未读通知后 unread-count 增加。"""
        _make_notif(db_session, test_user.id)
        _make_notif(db_session, test_user.id)
        r = client.get("/api/notifications/unread-count", headers=auth(user_token))
        assert r.json()["count"] == 2

    def test_mark_read(self, client, db_session, test_user, user_token):
        """PATCH /{id}/read 将通知标记为已读。"""
        n = _make_notif(db_session, test_user.id)
        r = client.patch(f"/api/notifications/{n.id}/read", headers=auth(user_token))
        assert r.status_code == 200
        assert r.json()["is_read"] is True
        assert r.json()["read_at"] is not None

    def test_mark_read_idempotent(self, client, db_session, test_user, user_token):
        """已读通知再次标记已读不报错。"""
        n = _make_notif(db_session, test_user.id, is_read=True)
        r = client.patch(f"/api/notifications/{n.id}/read", headers=auth(user_token))
        assert r.status_code == 200
        assert r.json()["is_read"] is True

    def test_mark_all_read(self, client, db_session, test_user, user_token):
        """PATCH /read-all 将所有未读通知标记为已读。"""
        _make_notif(db_session, test_user.id)
        _make_notif(db_session, test_user.id)
        r = client.patch("/api/notifications/read-all", headers=auth(user_token))
        assert r.status_code == 200
        # 验证未读数归零
        r2 = client.get("/api/notifications/unread-count", headers=auth(user_token))
        assert r2.json()["count"] == 0

    def test_delete_notification(self, client, db_session, test_user, user_token):
        """DELETE /{id} 删除通知，列表变空。"""
        n = _make_notif(db_session, test_user.id)
        r = client.delete(f"/api/notifications/{n.id}", headers=auth(user_token))
        assert r.status_code == 204
        # 再查列表为空
        r2 = client.get("/api/notifications", headers=auth(user_token))
        assert r2.json()["total"] == 0

    def test_unread_only_filter(self, client, db_session, test_user, user_token):
        """unread_only=true 只返回未读通知。"""
        _make_notif(db_session, test_user.id, is_read=False)
        _make_notif(db_session, test_user.id, is_read=True)
        r = client.get("/api/notifications?unread_only=true", headers=auth(user_token))
        data = r.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["is_read"] is False

    def test_no_auth_returns_401(self, client):
        """无 token 请求返回 401。"""
        assert client.get("/api/notifications").status_code == 401
        assert client.get("/api/notifications/unread-count").status_code == 401


# ─── TestNotificationPermissions ─────────────────────────────────────────────

class TestNotificationPermissions:
    """用户只能操作自己的通知。"""

    def test_cannot_read_others_notification(
        self, client, db_session, test_user, another_user_token
    ):
        """用户 A 的通知，用户 B 访问得到 404。"""
        n = _make_notif(db_session, test_user.id)
        r = client.patch(f"/api/notifications/{n.id}/read", headers=auth(another_user_token))
        assert r.status_code == 404

    def test_cannot_delete_others_notification(
        self, client, db_session, test_user, another_user_token
    ):
        """用户 A 的通知，用户 B 删除得到 404。"""
        n = _make_notif(db_session, test_user.id)
        r = client.delete(f"/api/notifications/{n.id}", headers=auth(another_user_token))
        assert r.status_code == 404

    def test_list_only_own_notifications(
        self, client, db_session, test_user, test_another_user, user_token, another_user_token
    ):
        """各用户的列表互相独立。"""
        _make_notif(db_session, test_user.id)
        _make_notif(db_session, test_another_user.id)
        _make_notif(db_session, test_another_user.id)
        r_a = client.get("/api/notifications", headers=auth(user_token))
        r_b = client.get("/api/notifications", headers=auth(another_user_token))
        assert r_a.json()["total"] == 1
        assert r_b.json()["total"] == 2


# ─── TestTaskAssignmentTrigger ────────────────────────────────────────────────

class TestTaskAssignmentTrigger:
    """活动任务指派触发站内通知。"""

    @pytest.fixture(autouse=True)
    def _setup(self, db_session: Session, test_user: User, test_another_user: User, test_community):
        """创建测试活动。"""
        from app.models.event import Event

        self.event = Event(
            title="测试活动",
            community_id=test_community.id,
            event_type="offline",
        )
        db_session.add(self.event)
        db_session.commit()
        db_session.refresh(self.event)

    def test_create_task_with_assignee_creates_notification(
        self, client, db_session, test_user, test_another_user, user_token, another_user_token
    ):
        """创建任务并指派给 test_another_user，对方收到通知。"""
        r = client.post(
            f"/api/events/{self.event.id}/tasks",
            json={"title": "整理材料", "assignee_ids": [test_another_user.id]},
            headers=auth(user_token),
        )
        assert r.status_code == 201

        # test_another_user 应有 1 条未读通知
        r2 = client.get("/api/notifications/unread-count", headers=auth(another_user_token))
        assert r2.json()["count"] == 1

        r3 = client.get("/api/notifications", headers=auth(another_user_token))
        items = r3.json()["items"]
        assert items[0]["type"] == NotificationType.TASK_ASSIGNED.value
        assert "整理材料" in items[0]["title"]

    def test_create_task_no_notification_to_self(
        self, client, db_session, test_user, user_token
    ):
        """将任务指派给自己，不产生通知。"""
        r = client.post(
            f"/api/events/{self.event.id}/tasks",
            json={"title": "自己的任务", "assignee_ids": [test_user.id]},
            headers=auth(user_token),
        )
        assert r.status_code == 201
        r2 = client.get("/api/notifications/unread-count", headers=auth(user_token))
        assert r2.json()["count"] == 0

    def test_update_task_assignee_creates_notification(
        self, client, db_session, test_user, test_another_user, user_token, another_user_token
    ):
        """更新任务的 assignee_id 时也触发通知。"""
        # 先创建无负责人的任务
        r = client.post(
            f"/api/events/{self.event.id}/tasks",
            json={"title": "待分配任务"},
            headers=auth(user_token),
        )
        task_id = r.json()["id"]

        # 更新 assignee_ids
        r2 = client.patch(
            f"/api/events/{self.event.id}/tasks/{task_id}",
            json={"assignee_ids": [test_another_user.id]},
            headers=auth(user_token),
        )
        assert r2.status_code == 200

        r3 = client.get("/api/notifications/unread-count", headers=auth(another_user_token))
        assert r3.json()["count"] == 1
