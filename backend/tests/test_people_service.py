"""人员 service 单元测试 — find_or_suggest()"""
from unittest.mock import MagicMock

from app.services.people_service import find_or_suggest


def _mock_person(pid: int = 1, display_name: str = "张三", github_handle: str = "zhangsan", company: str = "OpenCom"):
    p = MagicMock()
    p.id = pid
    p.display_name = display_name
    p.github_handle = github_handle
    p.company = company
    return p


class TestFindOrSuggestGithubMatch:
    """优先级 1：github_handle 精确匹配 → matched"""

    def test_github_matched(self):
        person = _mock_person()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = person

        result = find_or_suggest(db, {"github_handle": "zhangsan"})

        assert result["status"] == "matched"
        assert result["person_id"] == 1
        assert result["candidates"] == []

    def test_github_case_insensitive(self):
        """行输入大写，但匹配仍能找到"""
        person = _mock_person()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = person

        result = find_or_suggest(db, {"github_handle": "ZhangSan"})

        assert result["status"] == "matched"


class TestFindOrSuggestEmailMatch:
    """优先级 2：email 精确匹配 → suggest"""

    def test_email_matched(self):
        person = _mock_person()
        db = MagicMock()
        # github query → None；email query → person
        db.query.return_value.filter.return_value.first.side_effect = [None, person]

        result = find_or_suggest(db, {"github_handle": "no_match", "email": "test@example.com"})

        assert result["status"] == "suggest"
        assert result["person_id"] is None
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["reason"] == "email"

    def test_email_matched_no_github(self):
        """没有 github_handle 字段时，直接走 email 分支"""
        person = _mock_person()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = person

        result = find_or_suggest(db, {"email": "test@example.com"})

        assert result["status"] == "suggest"
        assert result["candidates"][0]["reason"] == "email"


class TestFindOrSuggestFuzzyName:
    """优先级 3：姓名+公司模糊匹配 → suggest"""

    def test_name_fuzzy_high_ratio(self):
        """ratio > 0.70 → suggest"""
        person = MagicMock()
        person.id = 2
        person.display_name = "张三"
        person.company = "OpenCom"

        db = MagicMock()
        # github / email 均无，所以不调用 first()
        # fuzzy 分支使用 .filter().limit() 迭代
        db.query.return_value.filter.return_value.limit.return_value = [person]

        result = find_or_suggest(db, {"display_name": "张三", "company": "OpenCom"})

        assert result["status"] == "suggest"
        assert len(result["candidates"]) >= 1
        assert result["candidates"][0]["reason"] == "name+company"

    def test_name_fuzzy_low_ratio_returns_new(self):
        """ratio <= 0.70 不进候选列表 → new"""
        person = MagicMock()
        person.id = 3
        person.display_name = "完全不同的姓名"
        person.company = "完全不同的公司"

        db = MagicMock()
        db.query.return_value.filter.return_value.limit.return_value = [person]

        result = find_or_suggest(db, {"display_name": "张三", "company": "OpenCom"})

        # 因为 ratio 很低，不进候选列表，最终 → new
        assert result["status"] == "new"

    def test_name_fuzzy_empty_candidates_returns_new(self):
        """候选列表为空 → new"""
        db = MagicMock()
        db.query.return_value.filter.return_value.limit.return_value = []

        result = find_or_suggest(db, {"display_name": "张三"})

        assert result["status"] == "new"


class TestFindOrSuggestNew:
    """优先级 4：均无匹配 → new"""

    def test_empty_row_returns_new(self):
        db = MagicMock()
        result = find_or_suggest(db, {})
        assert result["status"] == "new"
        assert result["person_id"] is None
        assert result["candidates"] == []

    def test_no_match_returns_new(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.limit.return_value = []

        result = find_or_suggest(
            db,
            {"github_handle": "ghost", "email": "ghost@test.com", "display_name": "幽灵"},
        )
        assert result["status"] == "new"

    def test_github_no_match_email_no_match_returns_new(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [None, None]
        db.query.return_value.filter.return_value.limit.return_value = []

        result = find_or_suggest(
            db, {"github_handle": "nobody", "email": "nobody@none.com"}
        )
        assert result["status"] == "new"
