"""
Test Suite: Authentication & Security

Covers:
  • Registration with password policy enforcement
  • Login flow (success + failure cases)
  • JWT token validation
  • Privilege escalation prevention
  • Role-based access control
  • Account deactivation guards
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.conftest import make_auth_header


# ══════════════════════════════════════════════════════════════════════════
# REGISTRATION TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestRegistration:
    """Tests for POST /api/v1/auth/register"""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Valid registration should return 201 with user data."""
        response = await client.post("/api/v1/auth/register", json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123!",
            "role": "candidate",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "john@example.com"
        assert data["role"] == "candidate"
        assert data["is_active"] is True
        # Password hash should NOT be in response
        assert "password_hash" not in data
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_register_weak_password_no_uppercase(self, client: AsyncClient):
        """Password without uppercase should be rejected."""
        response = await client.post("/api/v1/auth/register", json={
            "name": "Weak User",
            "email": "weak@example.com",
            "password": "weakpass123!",
            "role": "candidate",
        })
        assert response.status_code == 400 or response.status_code == 422
        # Should mention uppercase requirement

    @pytest.mark.asyncio
    async def test_register_weak_password_no_digit(self, client: AsyncClient):
        """Password without digits should be rejected."""
        response = await client.post("/api/v1/auth/register", json={
            "name": "Weak User",
            "email": "weak2@example.com",
            "password": "WeakPass!!!",
            "role": "candidate",
        })
        assert response.status_code == 400 or response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_weak_password_too_short(self, client: AsyncClient):
        """Password shorter than 8 chars should be rejected."""
        response = await client.post("/api/v1/auth/register", json={
            "name": "Short Pass",
            "email": "short@example.com",
            "password": "Ab1!",
            "role": "candidate",
        })
        assert response.status_code == 400 or response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, candidate_user):
        """Registering with an existing email should fail with 400."""
        response = await client.post("/api/v1/auth/register", json={
            "name": "Duplicate",
            "email": "candidate@test.com",  # Already exists
            "password": "ValidPass123!",
            "role": "candidate",
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Invalid email format should be rejected."""
        response = await client.post("/api/v1/auth/register", json={
            "name": "Bad Email",
            "email": "not-an-email",
            "password": "ValidPass123!",
            "role": "candidate",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_role(self, client: AsyncClient):
        """Invalid role should be rejected."""
        response = await client.post("/api/v1/auth/register", json={
            "name": "Bad Role",
            "email": "badrole@example.com",
            "password": "ValidPass123!",
            "role": "superuser",  # Not a valid role
        })
        assert response.status_code == 422


# ══════════════════════════════════════════════════════════════════════════
# LOGIN TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestLogin:
    """Tests for POST /api/v1/auth/login"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, candidate_user):
        """Valid credentials should return tokens."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "candidate@test.com",
            "password": "TestPass123!",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert data["user"]["email"] == "candidate@test.com"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, candidate_user):
        """Wrong password should return 401 with generic message."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "candidate@test.com",
            "password": "WrongPassword123!",
        })
        assert response.status_code == 401
        detail = response.json()["detail"]
        # Should NOT reveal whether email exists
        assert "incorrect email or password" in detail.lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Non-existent email should return same 401 (no email enumeration)."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "AnyPass123!",
        })
        assert response.status_code == 401
        detail = response.json()["detail"]
        # Same message as wrong password — prevents enumeration
        assert "incorrect email or password" in detail.lower()

    @pytest.mark.asyncio
    async def test_login_deactivated_user(self, client: AsyncClient, db_session):
        """Deactivated users should not be able to login."""
        from backend.models.user import User, UserRole
        from backend.services.auth_service import hash_password

        inactive_user = User(
            name="Inactive",
            email="inactive@test.com",
            password_hash=hash_password("ValidPass123!"),
            role=UserRole.CANDIDATE.value,
            is_active=False,
        )
        db_session.add(inactive_user)
        await db_session.flush()

        response = await client.post("/api/v1/auth/login", json={
            "email": "inactive@test.com",
            "password": "ValidPass123!",
        })
        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# JWT & AUTH GUARD TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestJWTAuth:
    """Tests for JWT token validation and protected routes."""

    @pytest.mark.asyncio
    async def test_protected_route_no_token(self, client: AsyncClient):
        """Accessing protected route without token should return 401."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_route_invalid_token(self, client: AsyncClient):
        """Invalid JWT token should return 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_route_valid_token(self, client: AsyncClient, candidate_user):
        """Valid JWT token should grant access to /me."""
        headers = make_auth_header(candidate_user)
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "candidate@test.com"

    @pytest.mark.asyncio
    async def test_expired_token_rejected(self, client: AsyncClient, candidate_user):
        """Expired tokens should be rejected."""
        import jwt as pyjwt
        from datetime import datetime, timedelta, timezone

        # Create an already-expired token
        payload = {
            "sub": str(candidate_user.id),
            "role": candidate_user.role,
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = pyjwt.encode(
            payload, "test_jwt_secret_key_for_unit_tests_only_128_chars_long_padding_here", algorithm="HS256"
        )

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# PRIVILEGE ESCALATION TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestPrivilegeEscalation:
    """Tests for role-based access and privilege escalation prevention."""

    @pytest.mark.asyncio
    async def test_candidate_cannot_list_users(self, client: AsyncClient, candidate_user):
        """Candidates should NOT be able to list all users."""
        headers = make_auth_header(candidate_user)
        response = await client.get("/api/v1/auth/users", headers=headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_list_users(self, client: AsyncClient, admin_user):
        """Admins should be able to list all users."""
        headers = make_auth_header(admin_user)
        response = await client.get("/api/v1/auth/users", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_recruiter_cannot_deactivate_admin(
        self, client: AsyncClient, recruiter_user, admin_user
    ):
        """CRITICAL: Recruiters must NOT be able to deactivate admins."""
        headers = make_auth_header(recruiter_user)
        response = await client.post(
            f"/api/v1/auth/users/{admin_user.id}/deactivate",
            headers=headers,
        )
        assert response.status_code == 403
        assert "recruiter" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_admin_can_deactivate_recruiter(
        self, client: AsyncClient, admin_user, recruiter_user
    ):
        """Admins should be able to deactivate recruiters."""
        headers = make_auth_header(admin_user)
        response = await client.post(
            f"/api/v1/auth/users/{recruiter_user.id}/deactivate",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_cannot_deactivate_self(self, client: AsyncClient, admin_user):
        """Users should NOT be able to deactivate their own account."""
        headers = make_auth_header(admin_user)
        response = await client.post(
            f"/api/v1/auth/users/{admin_user.id}/deactivate",
            headers=headers,
        )
        assert response.status_code == 400
        assert "own" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_candidate_cannot_deactivate_anyone(
        self, client: AsyncClient, candidate_user, recruiter_user
    ):
        """Candidates should NOT have access to deactivation endpoint."""
        headers = make_auth_header(candidate_user)
        response = await client.post(
            f"/api/v1/auth/users/{recruiter_user.id}/deactivate",
            headers=headers,
        )
        assert response.status_code == 403
