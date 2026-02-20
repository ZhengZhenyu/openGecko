"""
测试示例 - 演示如何使用各种 fixtures

这个文件包含了使用 conftest.py 中定义的各种 fixtures 的示例。
可以作为编写新测试时的参考模板。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Community
from app.models.content import Content
from app.core.security import verify_password, create_access_token


# ==============================================================================
# 数据库 Fixtures 示例
# ==============================================================================


def test_db_session_example(db_session: Session):
    """
    示例：使用 db_session fixture

    db_session 提供一个数据库会话，测试结束后自动回滚所有更改。
    每个测试函数都有独立的会话，确保测试隔离。
    """
    # 在测试数据库中创建新用户
    new_user = User(
        username="example_user",
        email="example@test.com",
        hashed_password="hashed_password_here",
        full_name="Example User",
        is_active=True,
    )
    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)

    # 验证用户已创建
    assert new_user.id is not None
    assert new_user.username == "example_user"

    # 测试结束后，这个用户会被自动删除（事务回滚）


def test_db_session_query_example(db_session: Session):
    """
    示例：在 db_session 中查询数据

    由于测试隔离，这个测试看不到上一个测试创建的用户。
    """
    # 查询所有用户
    users = db_session.query(User).all()

    # 由于测试隔离，这里应该是空的（或只有 fixture 创建的用户）
    # 上一个测试创建的用户已经回滚
    for user in users:
        print(f"Found user: {user.username}")


# ==============================================================================
# FastAPI TestClient Fixture 示例
# ==============================================================================


def test_client_basic_example(client: TestClient):
    """
    示例：使用 client fixture 测试 API 端点

    client 是 FastAPI 的 TestClient，自动注入测试数据库会话。
    """
    # 测试健康检查端点（不需要认证）
    response = client.get("/api/health")

    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_client_post_example(client: TestClient):
    """
    示例：使用 client 测试 POST 请求
    """
    # 发送 POST 请求
    response = client.post(
        "/api/some-endpoint",
        json={"key": "value"},
    )

    # 根据实际 API 验证响应
    # assert response.status_code == 200


# ==============================================================================
# 测试数据 Fixtures 示例
# ==============================================================================


def test_test_user_example(test_user: User):
    """
    示例：使用 test_user fixture

    test_user 是预先创建的测试用户，无需手动创建。
    """
    # 验证测试用户属性
    assert test_user.username == "testuser"
    assert test_user.email == "testuser@example.com"
    assert test_user.is_active is True
    assert test_user.is_superuser is False

    # 验证密码（原始密码是 "testpass123"）
    assert verify_password("testpass123", test_user.hashed_password)


def test_test_superuser_example(test_superuser: User):
    """
    示例：使用 test_superuser fixture

    test_superuser 是预先创建的超级管理员用户。
    """
    assert test_superuser.username == "admin"
    assert test_superuser.is_superuser is True

    # 超级管理员有特殊权限
    # 可以用于测试需要管理员权限的功能


def test_test_community_example(test_community: Community):
    """
    示例：使用 test_community fixture

    test_community 是预先创建的测试社区。
    """
    assert test_community.name == "Test Community"
    assert test_community.slug == "test-community"
    assert test_community.is_active is True


def test_combined_fixtures_example(
    db_session: Session,
    test_user: User,
    test_community: Community,
):
    """
    示例：组合使用多个 fixtures

    可以在同一个测试中使用多个 fixtures。
    """
    # 使用测试用户和社区创建内容
    content = Content(
        title="Example Content",
        content_markdown="This is example content",
        source_type="contribution",
        owner_id=test_user.id,
        community_id=test_community.id,
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    # 验证内容
    assert content.id is not None
    assert content.owner_id == test_user.id
    assert content.community_id == test_community.id


# ==============================================================================
# 认证 Fixtures 示例
# ==============================================================================


def test_user_token_example(user_token: str):
    """
    示例：使用 user_token fixture

    user_token 是 test_user 的 JWT token。
    """
    # token 是一个字符串
    assert isinstance(user_token, str)
    assert len(user_token) > 0

    # 可以手动构造 headers
    headers = {"Authorization": f"Bearer {user_token}"}
    # 然后用于 API 请求


def test_auth_headers_example(client: TestClient, auth_headers: dict):
    """
    示例：使用 auth_headers fixture 测试需要认证的端点

    auth_headers 包含 Authorization header 和 X-Community-Id header。
    """
    # 测试需要认证的端点
    response = client.get("/api/auth/me", headers=auth_headers)

    # 应该返回当前用户信息
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == "testuser"


def test_superuser_auth_headers_example(
    client: TestClient,
    superuser_auth_headers: dict,
):
    """
    示例：使用 superuser_auth_headers 测试管理员端点
    """
    # 测试只有超级管理员才能访问的端点
    response = client.get("/api/auth/users", headers=superuser_auth_headers)

    # 应该成功返回用户列表
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)


# ==============================================================================
# 测试隔离示例
# ==============================================================================


def test_isolation_test_1(db_session: Session, test_user: User):
    """
    示例：测试隔离 - 第一个测试

    这个测试修改了 test_user，但不会影响其他测试。
    """
    # 修改用户全名
    original_name = test_user.full_name
    test_user.full_name = "Modified Name"
    db_session.commit()

    # 在这个测试中，更改是可见的
    db_session.refresh(test_user)
    assert test_user.full_name == "Modified Name"

    # 测试结束后会回滚


def test_isolation_test_2(test_user: User):
    """
    示例：测试隔离 - 第二个测试

    即使上一个测试修改了 test_user，这个测试看到的是原始数据。
    """
    # 由于事务回滚，这里看到的是原始值
    assert test_user.full_name == "Test User"
    # 不是上一个测试中的 "Modified Name"


# ==============================================================================
# 参数化测试示例
# ==============================================================================


@pytest.mark.parametrize(
    "username,email,is_valid",
    [
        ("user1", "user1@example.com", True),
        ("user2", "user2@example.com", True),
        ("user3", "user3@example.com", True),
        ("", "invalid@example.com", False),  # 空用户名
        ("user4", "", False),  # 空邮箱
    ],
)
def test_parametrized_user_creation_example(
    db_session: Session,
    username: str,
    email: str,
    is_valid: bool,
):
    """
    示例：参数化测试

    使用 @pytest.mark.parametrize 可以用不同参数运行同一个测试。
    这个测试会运行 5 次，每次使用不同的参数。
    """
    if is_valid:
        # 有效输入应该成功创建用户
        user = User(
            username=username,
            email=email,
            hashed_password="test_hash",
            full_name="Test User",
        )
        db_session.add(user)
        db_session.commit()
        assert user.id is not None
    else:
        # SQLite 不对空字符串做约束，直接跳过这种验证场景
        pytest.skip("SQLite does not enforce empty string constraints")


# ==============================================================================
# 测试标记示例
# ==============================================================================


@pytest.mark.unit
def test_marked_as_unit():
    """
    示例：标记为单元测试

    运行方式：pytest -m unit
    """
    assert 1 + 1 == 2


@pytest.mark.api
@pytest.mark.auth
def test_marked_as_api_and_auth(client: TestClient):
    """
    示例：多个标记

    运行方式：pytest -m "api and auth"
    """
    # 测试 API 认证端点
    response = client.get("/api/auth/status")
    assert response.status_code == 200


@pytest.mark.slow
def test_marked_as_slow():
    """
    示例：标记为慢速测试

    跳过运行：pytest -m "not slow"
    """
    import time
    time.sleep(0.1)  # 模拟慢速操作
    assert True


@pytest.mark.integration
def test_marked_as_integration(
    client: TestClient,
    auth_headers: dict,
    db_session: Session,
    test_user: User,
    test_community: Community,
):
    """
    示例：标记为集成测试

    集成测试通常涉及多个组件的交互。
    运行方式：pytest -m integration
    """
    # 1. 创建内容
    content = Content(
        title="Integration Test Content",
        content_markdown="Testing integration",
        source_type="contribution",
        owner_id=test_user.id,
        community_id=test_community.id,
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    # 2. 通过 API 获取内容（使用正确的内容 API）
    response = client.get(
        f"/api/contents/{content.id}",
        headers=auth_headers,
    )

    # 3. 验证完整流程
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Integration Test Content"


# ==============================================================================
# 异步测试示例
# ==============================================================================


@pytest.mark.asyncio
async def test_async_example():
    """
    示例：异步测试

    由于配置了 asyncio_mode = auto，可以直接编写异步测试。
    """
    # 模拟异步操作
    async def async_operation():
        return "result"

    result = await async_operation()
    assert result == "result"


# ==============================================================================
# 异常测试示例
# ==============================================================================


def test_exception_example():
    """
    示例：测试异常

    使用 pytest.raises 验证代码应该抛出特定异常。
    """
    with pytest.raises(ValueError):
        raise ValueError("Expected error")


def test_exception_with_match_example():
    """
    示例：测试异常消息

    可以使用 match 参数验证异常消息。
    """
    with pytest.raises(ValueError, match="specific message"):
        raise ValueError("specific message in the error")


# ==============================================================================
# Fixture 依赖示例
# ==============================================================================


@pytest.fixture
def custom_content(db_session: Session, test_user: User, test_community: Community):
    """
    示例：自定义 fixture

    可以创建依赖其他 fixtures 的自定义 fixture。
    """
    content = Content(
        title="Custom Fixture Content",
        content_markdown="Created by custom fixture",
        source_type="contribution",
        owner_id=test_user.id,
        community_id=test_community.id,
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)
    return content


def test_custom_fixture_example(custom_content: Content):
    """
    示例：使用自定义 fixture
    """
    assert custom_content.title == "Custom Fixture Content"
    assert custom_content.id is not None


# ==============================================================================
# 多社区隔离测试示例
# ==============================================================================


def test_community_isolation_example(
    client: TestClient,
    auth_headers: dict,
    another_user_auth_headers: dict,
    test_community: Community,
    test_another_community: Community,
    db_session: Session,
    test_user: User,
    test_another_user: User,
):
    """
    示例：测试多社区之间的数据隔离

    确保一个社区的用户无法访问另一个社区的资源。
    """
    # test_user 在 test_community 中创建内容
    content = Content(
        title="Community 1 Content",
        content_markdown="This belongs to community 1",
        source_type="contribution",
        owner_id=test_user.id,
        community_id=test_community.id,
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    # test_user 应该能访问自己社区的内容
    response = client.get(
        f"/api/contents/{content.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200

    # test_another_user 不应该能访问其他社区的内容
    response = client.get(
        f"/api/contents/{content.id}",
        headers=another_user_auth_headers,
    )
    # 应该返回 403 或 404（取决于实现）
    assert response.status_code in [403, 404]


# ==============================================================================
# 实用技巧
# ==============================================================================


def test_debugging_example(test_user: User):
    """
    示例：调试技巧

    运行测试时添加 -s 参数可以看到 print 输出：
    pytest tests/test_example.py::test_debugging_example -s
    """
    print(f"\nDebugging: test_user.id = {test_user.id}")
    print(f"Debugging: test_user.username = {test_user.username}")

    # 在测试中添加 breakpoint() 可以进入调试器
    # breakpoint()

    assert test_user.username == "testuser"


def test_skip_example():
    """
    示例：跳过测试

    使用 @pytest.mark.skip 可以跳过测试。
    """
    pytest.skip("Skipping this test for demonstration")


@pytest.mark.skipif(True, reason="Conditional skip")
def test_conditional_skip_example():
    """
    示例：条件跳过

    根据条件决定是否跳过测试。
    """
    assert True


# ==============================================================================
# 最佳实践总结
# ==============================================================================

"""
测试编写最佳实践：

1. 测试名称应该清晰描述测试内容
   ✅ test_user_login_with_valid_credentials
   ❌ test_1

2. 每个测试应该测试一个具体功能
   ✅ 一个测试验证登录成功
   ✅ 另一个测试验证登录失败
   ❌ 一个测试验证登录的所有情况

3. 使用 fixtures 避免重复代码
   ✅ 使用 test_user fixture
   ❌ 在每个测试中手动创建用户

4. 确保测试隔离
   ✅ 使用 db_session 的事务回滚
   ❌ 在测试之间共享数据库状态

5. 使用适当的断言
   ✅ assert response.status_code == 200
   ❌ assert response.status_code  # 不清晰

6. 添加清晰的文档字符串
   ✅ 说明测试的目的和预期行为
   ❌ 没有文档或文档不清晰

7. 使用标记分类测试
   ✅ @pytest.mark.api, @pytest.mark.slow
   ❌ 所有测试混在一起

8. 参数化相似的测试
   ✅ 使用 @pytest.mark.parametrize
   ❌ 复制粘贴相似的测试函数

9. 测试边界条件和异常情况
   ✅ 测试空输入、超长输入、无效输入
   ❌ 只测试正常情况

10. 保持测试简洁
    ✅ 专注于测试逻辑
    ❌ 过多的设置代码
"""
