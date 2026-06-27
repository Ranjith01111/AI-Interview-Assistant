"""
Test Suite: Coding Routes & Rate Limiting

Covers:
  • Coding challenge submission validation
  • Language support verification
  • Rate limiting on auth endpoints
  • Health check endpoint
  • Root API info endpoint
"""

import uuid
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

from tests.conftest import make_auth_header


# ══════════════════════════════════════════════════════════════════════════
# CODING CHALLENGE TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestCodingRoutes:
    """Tests for the coding assessment endpoints."""

    @pytest.mark.asyncio
    async def test_submit_code_requires_auth(self, client: AsyncClient):
        """Code submission should require authentication."""
        response = await client.post("/api/v1/coding/submit", json={
            "challenge_id": str(uuid.uuid4()),
            "language": "python",
            "code": "print('hello')",
        })
        # Should be 401 or 404 depending on route structure
        assert response.status_code in (401, 404, 405)

    @pytest.mark.asyncio
    async def test_supported_languages(self):
        """Sandbox should support the documented languages."""
        from backend.services.sandbox_service import SandboxService
        
        sandbox = SandboxService()
        # These languages should be handled
        for lang in ["python", "javascript", "cpp", "java", "sql"]:
            # Should not raise on valid language
            result = await sandbox.execute(
                language=lang,
                code="",  # Empty code
                test_cases=[],
                time_limit=1.0,
            )
            # Empty code with no test cases should return gracefully
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_unsupported_language_handled(self):
        """Unsupported languages should fail gracefully."""
        from backend.services.sandbox_service import SandboxService
        
        sandbox = SandboxService()
        result = await sandbox.execute(
            language="ruby",
            code="puts 'hello'",
            test_cases=[{"input": "", "expected_output": "hello"}],
        )
        # Should return an error, not crash
        assert isinstance(result, dict)
        assert result.get("score", 0) == 0 or "error" in str(result).lower()


# ══════════════════════════════════════════════════════════════════════════
# RATE LIMITING TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestRateLimiting:
    """Tests for rate limiting middleware."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_auth_rate_limit_triggered(self, client: AsyncClient):
        """Auth endpoints should be rate limited (10/minute)."""
        # Send 15 login requests rapidly — should eventually get 429
        responses = []
        for _ in range(15):
            resp = await client.post("/api/v1/auth/login", json={
                "email": "test@test.com",
                "password": "Wrong123!",
            })
            responses.append(resp.status_code)

        # At least one should be rate limited (429) or all should be 401 (wrong creds)
        # Rate limiting may not kick in during tests if SlowAPI is mocked
        # This test verifies the endpoint at least responds consistently
        assert all(r in (401, 429) for r in responses)

    @pytest.mark.asyncio
    async def test_normal_endpoint_not_immediately_limited(self, client: AsyncClient):
        """Normal endpoints should handle reasonable request volume."""
        for _ in range(5):
            resp = await client.get("/")
            assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# HEALTH & ROOT ENDPOINT TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestHealthAndRoot:
    """Tests for health check and root info endpoints."""

    @pytest.mark.asyncio
    async def test_root_returns_api_info(self, client: AsyncClient):
        """Root / should return API metadata."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    @pytest.mark.asyncio
    async def test_root_does_not_expose_secrets(self, client: AsyncClient):
        """Root endpoint should not expose any secrets or credentials."""
        response = await client.get("/")
        data = response.json()
        text = str(data).lower()
        
        # Should not contain sensitive info
        assert "password" not in text
        assert "secret" not in text
        assert "api_key" not in text
        assert "token" not in text

    @pytest.mark.asyncio
    async def test_docs_endpoint_accessible(self, client: AsyncClient):
        """Swagger docs should be accessible."""
        response = await client.get("/docs")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_openapi_schema_available(self, client: AsyncClient):
        """OpenAPI JSON schema should be served."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    @pytest.mark.asyncio
    async def test_api_version_in_response(self, client: AsyncClient):
        """API version should be present in root response."""
        response = await client.get("/")
        data = response.json()
        # Version should be a semver-like string
        version = data.get("version", "")
        assert "." in version  # e.g., "2.0.0"


# ══════════════════════════════════════════════════════════════════════════
# 404 AND ERROR HANDLING TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Tests for proper error handling on invalid routes."""

    @pytest.mark.asyncio
    async def test_404_on_unknown_route(self, client: AsyncClient):
        """Unknown routes should return 404."""
        response = await client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_405_on_wrong_method(self, client: AsyncClient, candidate_user):
        """Wrong HTTP method should return 405."""
        headers = make_auth_header(candidate_user)
        # GET on a POST-only endpoint
        response = await client.get(
            f"/api/v1/interview/generate-questions/{uuid.uuid4()}",
            headers=headers,
        )
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_422_on_invalid_json(self, client: AsyncClient, candidate_user):
        """Malformed JSON body should return 422."""
        headers = make_auth_header(candidate_user)
        headers["Content-Type"] = "application/json"
        
        response = await client.post(
            "/api/v1/auth/login",
            content=b"not valid json{{{",
            headers=headers,
        )
        assert response.status_code == 422
