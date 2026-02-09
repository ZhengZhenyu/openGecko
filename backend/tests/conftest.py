"""
Pytest configuration and shared fixtures for API tests.
"""

import os
import tempfile
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.community import Community
from app.core.security import get_password_hash, create_access_token


# Test database setup
@pytest.fixture(scope="session")
def test_db_file():
    """Create a temporary database file for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="session")
def test_engine(test_db_file):
    """Create a test database engine."""
    engine = create_engine(
        f"sqlite:///{test_db_file}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Test data fixtures
@pytest.fixture(scope="function")
def test_community(db_session: Session) -> Community:
    """Create a test community."""
    community = Community(
        name="Test Community",
        slug="test-community",
        description="A test community for API testing",
        is_active=True,
    )
    db_session.add(community)
    db_session.commit()
    db_session.refresh(community)
    return community


@pytest.fixture(scope="function")
def test_user(db_session: Session, test_community: Community) -> User:
    """Create a test regular user."""
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    user.communities.append(test_community)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_superuser(db_session: Session, test_community: Community) -> User:
    """Create a test superuser."""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    user.communities.append(test_community)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_another_community(db_session: Session) -> Community:
    """Create another test community for isolation testing."""
    community = Community(
        name="Another Community",
        slug="another-community",
        description="Another test community",
        is_active=True,
    )
    db_session.add(community)
    db_session.commit()
    db_session.refresh(community)
    return community


@pytest.fixture(scope="function")
def test_another_user(db_session: Session, test_another_community: Community) -> User:
    """Create a user in another community for isolation testing."""
    user = User(
        username="anotheruser",
        email="another@example.com",
        hashed_password=get_password_hash("pass123"),
        full_name="Another User",
        is_active=True,
        is_superuser=False,
    )
    user.communities.append(test_another_community)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# Authentication fixtures
@pytest.fixture(scope="function")
def user_token(test_user: User) -> str:
    """Generate JWT token for test user."""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture(scope="function")
def superuser_token(test_superuser: User) -> str:
    """Generate JWT token for test superuser."""
    return create_access_token(data={"sub": test_superuser.username})


@pytest.fixture(scope="function")
def another_user_token(test_another_user: User) -> str:
    """Generate JWT token for another user."""
    return create_access_token(data={"sub": test_another_user.username})


@pytest.fixture(scope="function")
def auth_headers(user_token: str, test_community: Community) -> dict:
    """Generate authentication headers for regular user."""
    return {
        "Authorization": f"Bearer {user_token}",
        "X-Community-Id": str(test_community.id),
    }


@pytest.fixture(scope="function")
def superuser_auth_headers(superuser_token: str, test_community: Community) -> dict:
    """Generate authentication headers for superuser."""
    return {
        "Authorization": f"Bearer {superuser_token}",
        "X-Community-Id": str(test_community.id),
    }


@pytest.fixture(scope="function")
def another_user_auth_headers(another_user_token: str, test_another_community: Community) -> dict:
    """Generate authentication headers for another user."""
    return {
        "Authorization": f"Bearer {another_user_token}",
        "X-Community-Id": str(test_another_community.id),
    }
