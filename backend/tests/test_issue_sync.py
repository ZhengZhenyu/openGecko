"""Issue sync service 单元测试"""
from unittest.mock import MagicMock, patch

from app.services.issue_sync import _fetch_github_issue_status_sync, run_issue_sync


class TestFetchGithubIssueStatusSync:
    """测试 _fetch_github_issue_status_sync 同步 HTTP 函数"""

    def test_returns_open_status(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"state": "open"}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.services.issue_sync.httpx.Client", return_value=mock_client):
            result = _fetch_github_issue_status_sync("owner/repo", 42)

        assert result == "open"

    def test_returns_closed_status(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"state": "closed"}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.services.issue_sync.httpx.Client", return_value=mock_client):
            result = _fetch_github_issue_status_sync("owner/repo", 1, token="mytoken")

        assert result == "closed"

    def test_non_200_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.services.issue_sync.httpx.Client", return_value=mock_client):
            result = _fetch_github_issue_status_sync("owner/repo", 99)

        assert result is None

    def test_http_exception_returns_none(self):
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("network error")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.services.issue_sync.httpx.Client", return_value=mock_client):
            result = _fetch_github_issue_status_sync("owner/repo", 5)

        assert result is None

    def test_missing_state_field_defaults_to_open(self):
        """GitHub API 返回 200 但 JSON 中没有 state 字段，默认 open"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}  # no 'state' key

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.services.issue_sync.httpx.Client", return_value=mock_client):
            result = _fetch_github_issue_status_sync("owner/repo", 7)

        assert result == "open"


class TestRunIssueSync:
    """测试 run_issue_sync 主逻辑"""

    def _make_link(self, repo: str, issue_number: int, platform: str = "github", status: str = "open"):
        link = MagicMock()
        link.repo = repo
        link.issue_number = issue_number
        link.platform = platform
        link.issue_status = status
        return link

    def test_no_links_returns_zeros(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.services.issue_sync.SessionLocal", return_value=mock_db):
            result = run_issue_sync()

        assert result == {"updated": 0, "skipped": 0, "errors": 0}
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    def test_updated_when_status_changes(self):
        link = self._make_link("owner/repo", 10, status="open")
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [link]

        with (
            patch("app.services.issue_sync.SessionLocal", return_value=mock_db),
            patch(
                "app.services.issue_sync._fetch_github_issue_status_sync",
                return_value="closed",
            ),
        ):
            result = run_issue_sync(github_token="token")

        assert result["updated"] == 1
        assert result["skipped"] == 0
        assert result["errors"] == 0
        assert link.issue_status == "closed"

    def test_skipped_when_status_unchanged(self):
        link = self._make_link("owner/repo", 11, status="open")
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [link]

        with (
            patch("app.services.issue_sync.SessionLocal", return_value=mock_db),
            patch(
                "app.services.issue_sync._fetch_github_issue_status_sync",
                return_value="open",  # 与现有状态相同
            ),
        ):
            result = run_issue_sync()

        assert result["skipped"] == 1
        assert result["updated"] == 0
        assert result["errors"] == 0

    def test_errors_when_fetch_returns_none(self):
        link = self._make_link("owner/repo", 12)
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [link]

        with (
            patch("app.services.issue_sync.SessionLocal", return_value=mock_db),
            patch(
                "app.services.issue_sync._fetch_github_issue_status_sync",
                return_value=None,
            ),
        ):
            result = run_issue_sync()

        assert result["errors"] == 1
        assert result["updated"] == 0

    def test_mixed_results(self):
        """一次同步：1 个更新 + 1 个跳过 + 1 个错误"""
        links = [
            self._make_link("r/r1", 1, status="open"),   # → closed: updated
            self._make_link("r/r2", 2, status="closed"),  # → closed: skipped
            self._make_link("r/r3", 3, status="open"),   # → None: error
        ]
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = links

        fetch_side_effects = ["closed", "closed", None]

        with (
            patch("app.services.issue_sync.SessionLocal", return_value=mock_db),
            patch(
                "app.services.issue_sync._fetch_github_issue_status_sync",
                side_effect=fetch_side_effects,
            ),
        ):
            result = run_issue_sync()

        assert result["updated"] == 1
        assert result["skipped"] == 1
        assert result["errors"] == 1

    def test_db_exception_triggers_rollback(self):
        """db.query 抛出异常时 rollback，且不抛出"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("db error")

        with patch("app.services.issue_sync.SessionLocal", return_value=mock_db):
            result = run_issue_sync()

        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()
        assert result == {"updated": 0, "skipped": 0, "errors": 0}
