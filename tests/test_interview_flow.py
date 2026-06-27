"""
Test Suite: Interview Flow & Error Handling

Covers:
  • Session ID validation (UUID format)
  • Question generation
  • Interview start/chat/summary lifecycle
  • Error messages don't leak internals
  • Input validation (empty answers, invalid IDs)
"""

import uuid
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

from tests.conftest import make_auth_header


# ══════════════════════════════════════════════════════════════════════════
# SESSION ID VALIDATION
# ══════════════════════════════════════════════════════════════════════════


class TestSessionIDValidation:
    """Tests for UUID validation on interview endpoints."""

    @pytest.mark.asyncio
    async def test_invalid_session_id_rejected(self, client: AsyncClient, candidate_user):
        """Non-UUID session IDs should return 400."""
        headers = make_auth_header(candidate_user)

        invalid_ids = [
            "not-a-uuid",
            "12345",
            "'; DROP TABLE users; --",  # SQL injection attempt
            "../../../etc/passwd",       # Path traversal attempt
            "<script>alert(1)</script>",  # XSS attempt
            "",
        ]

        for bad_id in invalid_ids:
            if not bad_id:
                continue  # Empty string handled by routing
            response = await client.post(
                f"/api/v1/interview/generate-questions/{bad_id}",
                headers=headers,
            )
            assert response.status_code == 400, f"Should reject: {bad_id}"
            assert "uuid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_valid_uuid_passes_validation(self, client: AsyncClient, candidate_user):
        """Valid UUID format should pass validation (even if session doesn't exist)."""
        headers = make_auth_header(candidate_user)
        valid_uuid = str(uuid.uuid4())

        response = await client.post(
            f"/api/v1/interview/generate-questions/{valid_uuid}",
            headers=headers,
        )
        # Should get 404 (session not found) not 400 (bad format)
        assert response.status_code in (404, 500)


# ══════════════════════════════════════════════════════════════════════════
# ERROR MESSAGE SANITIZATION
# ══════════════════════════════════════════════════════════════════════════


class TestErrorSanitization:
    """Tests that internal error details are never exposed to clients."""

    @pytest.mark.asyncio
    async def test_500_error_no_stack_trace(self, client: AsyncClient, candidate_user):
        """500 errors should not contain stack traces or internal details."""
        headers = make_auth_header(candidate_user)
        valid_uuid = str(uuid.uuid4())

        # This will trigger an error since the session doesn't exist in expected ways
        response = await client.post(
            f"/api/v1/interview/start/{valid_uuid}",
            headers=headers,
        )

        if response.status_code == 500:
            detail = response.json().get("detail", "")
            # Should NOT contain Python error details
            assert "Traceback" not in detail
            assert "File \"" not in detail
            assert "line " not in detail
            assert "Error(" not in detail
            # Should be user-friendly
            assert "try again" in detail.lower() or "contact support" in detail.lower()

    @pytest.mark.asyncio
    async def test_generate_questions_error_sanitized(self, client: AsyncClient, candidate_user):
        """Question generation errors should not leak internals."""
        headers = make_auth_header(candidate_user)
        valid_uuid = str(uuid.uuid4())

        response = await client.post(
            f"/api/v1/interview/generate-questions/{valid_uuid}",
            headers=headers,
        )

        if response.status_code == 500:
            detail = response.json().get("detail", "")
            # Must not contain the raw exception string
            assert "NoneType" not in detail
            assert "AttributeError" not in detail
            assert "KeyError" not in detail

    @pytest.mark.asyncio
    async def test_summary_error_sanitized(self, client: AsyncClient, candidate_user):
        """Summary endpoint errors should not leak internals."""
        headers = make_auth_header(candidate_user)
        valid_uuid = str(uuid.uuid4())

        response = await client.get(
            f"/api/v1/interview/summary/{valid_uuid}",
            headers=headers,
        )

        if response.status_code == 500:
            detail = response.json().get("detail", "")
            assert "sqlalchemy" not in detail.lower()
            assert "redis" not in detail.lower()


# ══════════════════════════════════════════════════════════════════════════
# CHAT INPUT VALIDATION
# ══════════════════════════════════════════════════════════════════════════


class TestChatInputValidation:
    """Tests for the POST /interview/chat endpoint input validation."""

    @pytest.mark.asyncio
    async def test_empty_answer_rejected(self, client: AsyncClient, candidate_user):
        """Empty or whitespace-only answers should be rejected."""
        headers = make_auth_header(candidate_user)

        response = await client.post("/api/v1/interview/chat", json={
            "session_id": str(uuid.uuid4()),
            "message": "",
        }, headers=headers)
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_whitespace_answer_rejected(self, client: AsyncClient, candidate_user):
        """Whitespace-only answers should be rejected."""
        headers = make_auth_header(candidate_user)

        response = await client.post("/api/v1/interview/chat", json={
            "session_id": str(uuid.uuid4()),
            "message": "   \n\t  ",
        }, headers=headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_session_id_rejected(self, client: AsyncClient, candidate_user):
        """Missing session_id should return 422."""
        headers = make_auth_header(candidate_user)

        response = await client.post("/api/v1/interview/chat", json={
            "message": "My answer is polymorphism",
        }, headers=headers)
        assert response.status_code == 422


# ══════════════════════════════════════════════════════════════════════════
# AUTH ENFORCEMENT ON INTERVIEW ROUTES
# ══════════════════════════════════════════════════════════════════════════


class TestInterviewAuthEnforcement:
    """Tests that interview routes require authentication."""

    @pytest.mark.asyncio
    async def test_generate_questions_requires_auth(self, client: AsyncClient):
        """Generate questions without auth should return 401."""
        response = await client.post(
            f"/api/v1/interview/generate-questions/{uuid.uuid4()}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_start_interview_requires_auth(self, client: AsyncClient):
        """Start interview without auth should return 401."""
        response = await client.post(
            f"/api/v1/interview/start/{uuid.uuid4()}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_requires_auth(self, client: AsyncClient):
        """Chat endpoint without auth should return 401."""
        response = await client.post("/api/v1/interview/chat", json={
            "session_id": str(uuid.uuid4()),
            "message": "test",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_summary_requires_auth(self, client: AsyncClient):
        """Summary endpoint without auth should return 401."""
        response = await client.get(
            f"/api/v1/interview/summary/{uuid.uuid4()}"
        )
        assert response.status_code == 401
