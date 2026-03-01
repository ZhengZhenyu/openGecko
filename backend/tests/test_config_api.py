"""Tests for GET /api/config/features endpoint"""
from unittest import mock

import pytest
from fastapi.testclient import TestClient

import app.main as main_module


class TestGetFeatures:
    def test_features_no_auth_required(self, client: TestClient):
        """该端点为公开端点，无需 Authorization header"""
        resp = client.get("/api/config/features")
        assert resp.status_code == 200

    def test_features_default_insights_enabled(self, client: TestClient):
        """默认情况下 insights_module 应为 True（与 settings 默认值一致）"""
        resp = client.get("/api/config/features")
        assert resp.status_code == 200
        data = resp.json()
        assert "insights_module" in data
        assert isinstance(data["insights_module"], bool)

    def test_features_insights_module_true(self, client: TestClient):
        """当 ENABLE_INSIGHTS_MODULE=True 时，接口返回 insights_module=true"""
        with mock.patch.object(main_module.settings, "ENABLE_INSIGHTS_MODULE", True):
            resp = client.get("/api/config/features")
        assert resp.status_code == 200
        assert resp.json()["insights_module"] is True

    def test_features_insights_module_false(self, client: TestClient):
        """当 ENABLE_INSIGHTS_MODULE=False 时，接口返回 insights_module=false"""
        with mock.patch.object(main_module.settings, "ENABLE_INSIGHTS_MODULE", False):
            resp = client.get("/api/config/features")
        assert resp.status_code == 200
        assert resp.json()["insights_module"] is False
