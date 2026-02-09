# 测试指南

本文档说明 OmniContent 后端的测试策略和运行方法。

## 测试结构

```
backend/tests/
├── __init__.py                  # 测试包初始化
├── conftest.py                  # Pytest 配置和共享 fixtures
├── test_auth_api.py             # 认证 API 测试
├── test_communities_api.py      # 社区管理 API 测试
├── test_contents_api.py         # 内容管理 API 测试
├── test_publish_api.py          # 发布管理 API 测试
├── test_analytics_api.py        # 数据分析 API 测试
└── test_auth_integration.py     # 认证和多租户集成测试
```

## 测试覆盖范围

### API 端点测试

| 测试文件 | 覆盖的 API 端点 | 测试数量 |
|---------|---------------|---------|
| `test_auth_api.py` | `/api/auth/*` | 14 |
| `test_communities_api.py` | `/api/communities/*` | 20+ |
| `test_contents_api.py` | `/api/contents/*` | 25+ |
| `test_publish_api.py` | `/api/publish/*` | 15+ |
| `test_analytics_api.py` | `/api/analytics/*` | 15+ |

### 测试类型

- **单元测试**: 测试单个函数和模块
- **集成测试**: 测试 API 端点和数据库交互
- **功能测试**: 测试完整的业务流程

### 测试覆盖的功能

✅ **认证和授权**
- 用户登录/注册
- JWT Token 生成和验证
- 密码哈希和验证
- 用户权限检查（普通用户 vs 超级用户）

✅ **多租户隔离**
- 社区级数据隔离
- 跨社区访问控制
- 社区成员管理

✅ **内容管理**
- CRUD 操作
- Markdown 到 HTML 转换
- 内容状态管理
- 分页和过滤
- 关键词搜索

✅ **发布管理**
- 多渠道发布（微信、Hugo、CSDN、知乎）
- 内容格式转换
- 发布记录追踪

✅ **数据分析**
- 统计数据准确性
- 渠道配置管理
- 社区级数据隔离

## 安装测试依赖

```bash
cd backend
pip install -r requirements-dev.txt
```

开发依赖包括：
- `pytest` - 测试框架
- `pytest-asyncio` - 异步测试支持
- `pytest-cov` - 代码覆盖率
- `pytest-mock` - Mock 支持
- `faker` - 测试数据生成

## 运行测试

### 运行所有测试

```bash
cd backend
pytest
```

### 运行特定测试文件

```bash
# 运行认证测试
pytest tests/test_auth_api.py

# 运行社区管理测试
pytest tests/test_communities_api.py

# 运行内容管理测试
pytest tests/test_contents_api.py
```

### 运行特定测试类

```bash
pytest tests/test_auth_api.py::TestLogin
```

### 运行特定测试函数

```bash
pytest tests/test_auth_api.py::TestLogin::test_login_success
```

### 使用标记过滤测试

```bash
# 只运行 API 测试
pytest -m api

# 跳过慢速测试
pytest -m "not slow"

# 只运行认证相关测试
pytest -m auth
```

### 详细输出

```bash
# 显示详细输出
pytest -v

# 显示每个测试的输出
pytest -s

# 显示失败测试的详细信息
pytest -vv
```

### 并行运行测试

```bash
# 安装 pytest-xdist
pip install pytest-xdist

# 使用 4 个进程并行运行
pytest -n 4
```

## 代码覆盖率

### 生成覆盖率报告

```bash
# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 查看 HTML 报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### 覆盖率目标

项目配置了 **80% 的最低覆盖率要求**。如果覆盖率低于 80%，测试将失败。

### 查看覆盖率报告

```bash
# 终端显示覆盖率
pytest --cov=app --cov-report=term-missing

# 显示未覆盖的行号
pytest --cov=app --cov-report=term-missing:skip-covered
```

## 测试 Fixtures

### 数据库 Fixtures

- `test_db_file`: 临时测试数据库文件
- `test_engine`: SQLAlchemy 测试引擎
- `db_session`: 测试数据库会话（函数级别，每个测试独立）

### 测试数据 Fixtures

- `test_community`: 测试社区
- `test_user`: 普通测试用户
- `test_superuser`: 超级用户
- `test_another_community`: 另一个社区（用于隔离测试）
- `test_another_user`: 另一个社区的用户

### 认证 Fixtures

- `user_token`: 普通用户的 JWT token
- `superuser_token`: 超级用户的 JWT token
- `auth_headers`: 包含 token 和 community ID 的请求头
- `superuser_auth_headers`: 超级用户的请求头

### HTTP 客户端 Fixture

- `client`: FastAPI TestClient 实例

## 编写新测试

### 基本测试结构

```python
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

class TestMyFeature:
    """Tests for my feature."""

    def test_something_success(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers: dict,
    ):
        """Test successful operation."""
        # Arrange
        # ... 准备测试数据

        # Act
        response = client.get("/api/my-endpoint", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "expected_value"
```

### 测试命名约定

- 测试文件: `test_<module>_api.py`
- 测试类: `Test<Feature>`
- 测试函数: `test_<scenario>_<expected_outcome>`

示例:
```python
def test_create_content_success(...)  # 成功场景
def test_create_content_invalid_data(...)  # 失败场景
def test_create_content_no_auth(...)  # 权限场景
```

### 测试场景清单

为每个 API 端点编写测试时，考虑以下场景：

✅ **成功场景**
- 正常的成功操作
- 边界条件

✅ **失败场景**
- 无效输入数据
- 不存在的资源 (404)
- 权限不足 (403)
- 未认证 (401)

✅ **数据隔离**
- 社区级数据隔离
- 跨社区访问拒绝

✅ **业务逻辑**
- 数据验证
- 状态转换
- 级联操作

## 持续集成

### GitHub Actions

测试在每次 push 和 pull request 时自动运行。查看 [`.github/workflows/backend-ci.yml`](../.github/workflows/backend-ci.yml)

### 本地 Pre-commit Hook

设置 pre-commit hook 在提交前自动运行测试：

```bash
# 创建 .git/hooks/pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
cd backend
pytest
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

## 故障排除

### 测试数据库问题

如果遇到数据库锁定或状态问题：

```bash
# 清理测试数据库
rm -f backend/*.db
pytest
```

### Import 错误

确保在 `backend/` 目录下运行测试：

```bash
cd backend
pytest
```

### 覆盖率未达到要求

查看未覆盖的代码：

```bash
pytest --cov=app --cov-report=term-missing:skip-covered
```

然后为未覆盖的代码添加测试。

## 最佳实践

### ✅ 推荐做法

1. **每个测试独立**: 不依赖其他测试的执行顺序
2. **使用 Fixtures**: 复用测试数据和配置
3. **清晰的测试名称**: 从名称就能理解测试目的
4. **AAA 模式**: Arrange（准备）→ Act（执行）→ Assert（断言）
5. **测试一个场景**: 每个测试只测试一个具体场景
6. **完整的覆盖**: 测试成功和失败场景

### ❌ 避免做法

1. **避免测试间依赖**: 不要依赖测试执行顺序
2. **避免硬编码数据**: 使用 fixtures 和工厂函数
3. **避免过度 Mock**: 优先使用真实的测试数据库
4. **避免忽略失败**: 所有测试都应该通过
5. **避免重复代码**: 使用 fixtures 和辅助函数

## 参考资源

- [Pytest 官方文档](https://docs.pytest.org/)
- [FastAPI 测试文档](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy 测试最佳实践](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#session-testing)

## 联系方式

如有测试相关问题，请在 GitHub Issues 中提出。
