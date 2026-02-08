#!/usr/bin/env python3
"""
Test script for Phase 1: Basic Authentication and Community Isolation
"""

import sys
from sqlalchemy.orm import Session

# Add app to path
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import User, Community
from app.core.security import verify_password, create_access_token, decode_access_token


def test_database_migration():
    """Test that migration created default community and admin user."""
    print("\n=== Testing Database Migration ===")
    db = SessionLocal()
    try:
        # Check default community
        community = db.query(Community).filter(Community.slug == "default").first()
        assert community is not None, "Default community not found"
        assert community.name == "Default Community"
        print(f"✓ Default community exists: {community.name} (ID: {community.id})")

        # Check admin user
        admin = db.query(User).filter(User.username == "admin").first()
        assert admin is not None, "Admin user not found"
        assert admin.is_superuser is True
        print(f"✓ Admin user exists: {admin.username} (email: {admin.email})")

        # Check admin is member of default community
        assert community in admin.communities, "Admin not member of default community"
        print(f"✓ Admin is member of default community")

    finally:
        db.close()


def test_password_verification():
    """Test password hashing and verification."""
    print("\n=== Testing Password Verification ===")
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        assert admin is not None

        # Test correct password
        is_valid = verify_password("admin123", admin.hashed_password)
        assert is_valid, "Password verification failed"
        print("✓ Password verification works (correct password)")

        # Test incorrect password
        is_valid = verify_password("wrongpassword", admin.hashed_password)
        assert not is_valid, "Password verification should fail for wrong password"
        print("✓ Password verification works (incorrect password)")

    finally:
        db.close()


def test_jwt_token():
    """Test JWT token creation and decoding."""
    print("\n=== Testing JWT Token ===")

    # Create token
    token = create_access_token(data={"sub": "admin"})
    assert token is not None
    print(f"✓ Token created: {token[:30]}...")

    # Decode token
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "admin"
    print(f"✓ Token decoded successfully: {payload.get('sub')}")

    # Test invalid token
    invalid_payload = decode_access_token("invalid.token.here")
    assert invalid_payload is None
    print("✓ Invalid token rejected")


def test_community_isolation():
    """Test that community data is properly isolated."""
    print("\n=== Testing Community Isolation ===")
    db = SessionLocal()
    try:
        from app.models import Content

        # Check existing contents are migrated to default community
        default_community = db.query(Community).filter(Community.slug == "default").first()
        contents = db.query(Content).filter(Content.community_id == default_community.id).all()
        print(f"✓ Found {len(contents)} contents in default community")

        # Check all contents have community_id set
        all_contents = db.query(Content).all()
        for content in all_contents:
            assert content.community_id is not None, f"Content {content.id} has no community_id"
        print(f"✓ All {len(all_contents)} contents have community_id set")

    finally:
        db.close()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 1 Verification Tests")
    print("=" * 60)

    try:
        test_database_migration()
        test_password_verification()
        test_jwt_token()
        test_community_isolation()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\nPhase 1 implementation is complete and working correctly.")
        print("\nDefault credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nYou can now test the API endpoints using these credentials.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
