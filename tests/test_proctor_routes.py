"""
Test Suite: Proctor Routes & Access Control

Covers:
  • Proctor frame analysis input validation
  • Session report access control (candidate can only see own)
  • Event logging validation
  • UUID validation on session_id
  • No auth on frame analysis (intentional — iframe restriction)
  • Auth required on session reports
"""

import uuid
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

from tests.conftest import make_auth_header


# ══════════════════════════════════════════════════════════════════════════
# PROCTOR FRAME ANALYSIS
# ══════════════════════════════════════════════════════════════════════════


class TestProctorFrameAnalysis:
    """Tests for POST /api/v1/proctor/analyze-frame"""

    @pytest.mark.asyncio
    async def test_analyze_frame_valid_input(self, client: AsyncClient):
        """Valid frame submission should not crash."""
        with patch("backend.routes.proctor_routes.proctor_service") as mock_ps:
            mock_ps.analyze_frame = AsyncMock(return_value={
                "success": True,
                "violations": [],
                "face_count": 1,
                "gaze": {"direction": "center"},
                "head_pose": {"pitch": 0, "yaw": 0},
                "objects": [],
                "mock_mode": True,
            })

            response = await client.post("/api/v1/proctor/analyze-frame", json={
                "session_id": str(uuid.uuid4()),
                "image_data": "base64encodedimagedata==",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "face_count" in data

    @pytest.mark.asyncio
    async def test_analyze_frame_missing_session_id(self, client: AsyncClient):
        """Missing session_id should return 422."""
        response = await client.post("/api/v1/proctor/analyze-frame", json={
            "image_data": "base64data==",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_frame_missing_image(self, client: AsyncClient):
        """Missing image_data should return 422."""
        response = await client.post("/api/v1/proctor/analyze-frame", json={
            "session_id": str(uuid.uuid4()),
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_frame_no_auth_required(self, client: AsyncClient):
        """Frame analysis should work without auth (iframe restriction)."""
        with patch("backend.routes.proctor_routes.proctor_service") as mock_ps:
            mock_ps.analyze_frame = AsyncMock(return_value={
                "success": True,
                "violations": [],
                "face_count": 1,
                "gaze": {},
                "head_pose": {},
                "objects": [],
                "mock_mode": True,
            })

            # No Authorization header
            response = await client.post("/api/v1/proctor/analyze-frame", json={
                "session_id": str(uuid.uuid4()),
                "image_data": "data",
            })
            # Should NOT return 401
            assert response.status_code != 401


# ══════════════════════════════════════════════════════════════════════════
# PROCTOR EVENT LOGGING
# ══════════════════════════════════════════════════════════════════════════


class TestProctorEventLogging:
    """Tests for POST /api/v1/proctor/log-event"""

    @pytest.mark.asyncio
    async def test_log_event_valid(self, client: AsyncClient):
        """Valid event log should succeed."""
        with patch("backend.routes.proctor_routes.proctor_service") as mock_ps:
            mock_ps.log_browser_event = AsyncMock(return_value={"success": True})

            response = await client.post("/api/v1/proctor/log-event", json={
                "session_id": str(uuid.uuid4()),
                "event_type": "tab_switch",
                "details": {"tab_title": "Google"},
            })
            assert response.status_code == 200
            assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_log_event_missing_type(self, client: AsyncClient):
        """Missing event_type should return 422."""
        response = await client.post("/api/v1/proctor/log-event", json={
            "session_id": str(uuid.uuid4()),
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_log_event_various_types(self, client: AsyncClient):
        """Various event types should be accepted."""
        with patch("backend.routes.proctor_routes.proctor_service") as mock_ps:
            mock_ps.log_browser_event = AsyncMock(return_value={"success": True})

            event_types = [
                "tab_switch",
                "window_minimize",
                "focus_loss",
                "copy_paste",
                "fullscreen_exit",
                "voice_detected",
            ]
            for event_type in event_types:
                response = await client.post("/api/v1/proctor/log-event", json={
                    "session_id": str(uuid.uuid4()),
                    "event_type": event_type,
                })
                assert response.status_code == 200, f"Failed for: {event_type}"


# ══════════════════════════════════════════════════════════════════════════
# SESSION REPORT ACCESS CONTROL
# ══════════════════════════════════════════════════════════════════════════


class TestProctorReportAccessControl:
    """Tests for GET /api/v1/proctor/session-report/{session_id}"""

    @pytest.mark.asyncio
    async def test_report_requires_auth(self, client: AsyncClient):
        """Session report should require authentication."""
        response = await client.get(
            f"/api/v1/proctor/session-report/{uuid.uuid4()}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_report_invalid_session_id(self, client: AsyncClient, candidate_user):
        """Invalid UUID should return 400."""
        headers = make_auth_header(candidate_user)
        response = await client.get(
            "/api/v1/proctor/session-report/not-a-uuid",
            headers=headers,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_report_nonexistent_session(self, client: AsyncClient, candidate_user):
        """Non-existent session should return 404."""
        headers = make_auth_header(candidate_user)
        response = await client.get(
            f"/api/v1/proctor/session-report/{uuid.uuid4()}",
            headers=headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_candidate_cannot_see_other_sessions(
        self, client: AsyncClient, candidate_user, db_session
    ):
        """Candidates should only see their own session reports."""
        from backend.models.interview import InterviewSession, SessionStatus
        
        # Create a session owned by a different user
        other_user_id = uuid.uuid4()
        session_id = uuid.uuid4()
        other_session = InterviewSession(
            id=session_id,
            candidate_name="Other Person",
            user_id=other_user_id,
            resume_text="Other resume",
            skills_detected=["python"],
            experience_years="3 years",
            status=SessionStatus.COMPLETED.value,
        )
        db_session.add(other_session)
        await db_session.flush()

        headers = make_auth_header(candidate_user)
        response = await client.get(
            f"/api/v1/proctor/session-report/{session_id}",
            headers=headers,
        )
        assert response.status_code == 403
        assert "denied" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_recruiter_can_see_any_session(
        self, client: AsyncClient, recruiter_user, db_session
    ):
        """Recruiters should be able to view any session report."""
        from backend.models.interview import InterviewSession, SessionStatus

        session_id = uuid.uuid4()
        session = InterviewSession(
            id=session_id,
            candidate_name="Some Candidate",
            user_id=uuid.uuid4(),  # Different user
            resume_text="Resume text",
            skills_detected=["java"],
            experience_years="2 years",
            status=SessionStatus.COMPLETED.value,
        )
        db_session.add(session)
        await db_session.flush()

        headers = make_auth_header(recruiter_user)
        response = await client.get(
            f"/api/v1/proctor/session-report/{session_id}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == str(session_id)
        assert "risk_level" in data
