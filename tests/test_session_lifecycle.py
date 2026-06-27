"""
Test Suite: Full End-to-End Interview Session Lifecycle

Covers:
  • Register → Login → Upload resume → Generate questions → Start interview →
    Answer all questions → Get summary
  • Session cleanup (delete_session_cache)
  • Redis state consistency through the lifecycle
  • Error cases: starting without questions, chatting without starting, etc.
  • Session ownership enforcement

Uses pytest + pytest-asyncio with the conftest fixtures (async SQLite + Redis mock + httpx AsyncClient).
"""

import io
import uuid
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient

from tests.conftest import make_auth_header


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════


SAMPLE_RESUME_TEXT = """
Alice Developer
Senior Software Engineer

Professional Summary
Experienced software engineer with 5+ years of experience building scalable web 
applications using Python, FastAPI, React, and PostgreSQL. Strong background in 
cloud infrastructure (AWS) and containerized deployments (Docker, Kubernetes).

Work Experience

Senior Software Engineer — TechCorp (2021 - Present)
- Built microservices architecture using FastAPI and Docker
- Deployed applications on AWS ECS with Terraform
- Implemented CI/CD pipelines using GitHub Actions

Software Developer — StartupABC (2019 - 2021)
- Developed React frontend with TypeScript
- Built REST APIs with Node.js and Express
- Used PostgreSQL and Redis for data layer

Education
B.Tech in Computer Science — Stanford (2019)

Skills
Python, FastAPI, React, TypeScript, Docker, Kubernetes, AWS, PostgreSQL, Redis,
Git, CI/CD, Terraform, Node.js, Express, REST APIs
"""


@pytest.fixture
def sample_pdf_bytes():
    """
    Create minimal PDF-like bytes for upload testing.
    In reality, the resume service will parse this; we mock the parsing.
    """
    # A minimal PDF file structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Alice Developer) Tj ET
endstream
endobj
xref
0 5
trailer
<< /Size 5 /Root 1 0 R >>
startxref
0
%%EOF"""
    return pdf_content


@pytest.fixture
def mock_resume_processing():
    """Mock the resume processing to return consistent results."""
    mock_session_id = str(uuid.uuid4())
    mock_metadata = {
        "candidate_name": "Alice Developer",
        "skills_detected": ["python", "fastapi", "react", "docker", "aws", "postgresql"],
        "experience_years": "5+",
    }

    with patch(
        "backend.routes.resume_routes.process_resume",
        new_callable=AsyncMock,
        return_value=(mock_session_id, mock_metadata),
    ) as mock_proc:
        yield {
            "mock": mock_proc,
            "session_id": mock_session_id,
            "metadata": mock_metadata,
        }


@pytest.fixture
def mock_questions_cache():
    """Standard questions cache that would be stored in Redis."""
    return [
        {
            "id": 1,
            "question": "What is the difference between a list and a tuple in Python?",
            "topic": "python_basics",
            "difficulty": "easy",
            "category": "python",
            "type": "technical",
            "expected_keywords": ["mutable", "immutable", "list", "tuple", "ordered"],
            "model_answer_hint": "Lists are mutable, tuples are immutable.",
            "project_reference": None,
        },
        {
            "id": 2,
            "question": "Explain how Docker containerization works.",
            "topic": "docker",
            "difficulty": "medium",
            "category": "docker",
            "type": "technical",
            "expected_keywords": ["container", "image", "isolation", "dockerfile", "layer"],
            "model_answer_hint": "Docker uses OS-level virtualization.",
            "project_reference": None,
        },
        {
            "id": 3,
            "question": "Tell me about a challenging project you worked on.",
            "topic": "behavioral",
            "difficulty": "medium",
            "category": "behavioral",
            "type": "hr",
            "expected_keywords": ["challenge", "solution", "result", "team", "learned"],
            "model_answer_hint": "Use STAR method.",
            "project_reference": None,
        },
    ]


# ══════════════════════════════════════════════════════════════════════════════
# FULL LIFECYCLE: REGISTER → UPLOAD → QUESTIONS → INTERVIEW → SUMMARY
# ══════════════════════════════════════════════════════════════════════════════


class TestFullInterviewLifecycle:
    """End-to-end lifecycle tests using HTTP endpoints."""

    @pytest.mark.asyncio
    async def test_register_and_login(self, client: AsyncClient):
        """Should be able to register a new user and login."""
        # Register
        reg_response = await client.post("/api/v1/auth/register", json={
            "name": "Lifecycle Test User",
            "email": "lifecycle@test.com",
            "password": "LifeCycle123!",
            "role": "candidate",
        })
        assert reg_response.status_code == 201, f"Register failed: {reg_response.json()}"
        reg_data = reg_response.json()
        assert reg_data["success"] is True
        assert "access_token" in reg_data

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "lifecycle@test.com",
            "password": "LifeCycle123!",
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        return login_data["access_token"]

    @pytest.mark.asyncio
    async def test_resume_upload(
        self, client: AsyncClient, candidate_user, sample_pdf_bytes, mock_resume_processing
    ):
        """Should upload a resume and get session_id back."""
        headers = make_auth_header(candidate_user)

        response = await client.post(
            "/api/v1/resume/upload",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == mock_resume_processing["session_id"]
        assert data["candidate_name"] == "Alice Developer"
        assert len(data["skills_detected"]) > 0

    @pytest.mark.asyncio
    async def test_generate_questions_after_upload(
        self, client: AsyncClient, candidate_user, db_session, mock_redis
    ):
        """Should generate questions for a valid session."""
        headers = make_auth_header(candidate_user)

        # Create a session in the database
        from backend.models.interview import InterviewSession, SessionStatus

        session = InterviewSession(
            candidate_name="Alice Developer",
            user_id=candidate_user.id,
            resume_text=SAMPLE_RESUME_TEXT,
            skills_detected=["python", "fastapi", "react", "docker"],
            experience_years="5+",
            status=SessionStatus.CREATED.value,
        )
        db_session.add(session)
        await db_session.flush()
        session_id = str(session.id)

        # Mock the session service calls
        with patch(
            "backend.services.question_service.session_service.get_session_meta",
            new_callable=AsyncMock,
            return_value={
                "session_id": session_id,
                "candidate_name": "Alice Developer",
                "skills": ["python", "fastapi", "react", "docker"],
                "experience": "5+",
                "resume_text": SAMPLE_RESUME_TEXT,
            },
        ), patch(
            "backend.services.question_service.session_service.get_parsed_resume",
            new_callable=AsyncMock,
            return_value={
                "skills": ["python", "fastapi", "react", "docker"],
                "experience_years": 5.0,
                "skill_categories": {"python": ["python", "fastapi"], "react": ["react"]},
            },
        ), patch(
            "backend.services.question_service.session_service.save_questions_cache",
            new_callable=AsyncMock,
        ):
            response = await client.post(
                f"/api/v1/interview/generate-questions/{session_id}",
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_questions"] >= 1
        assert len(data["questions"]) >= 1
        # Each question should have required fields
        for q in data["questions"]:
            assert "question" in q
            assert "difficulty" in q

    @pytest.mark.asyncio
    async def test_start_interview(
        self, client: AsyncClient, candidate_user, db_session,
        mock_redis, mock_questions_cache
    ):
        """Should start the interview and return the first question."""
        headers = make_auth_header(candidate_user)

        # Create session in DB
        from backend.models.interview import InterviewSession, SessionStatus

        session = InterviewSession(
            candidate_name="Alice Developer",
            user_id=candidate_user.id,
            resume_text=SAMPLE_RESUME_TEXT,
            skills_detected=["python"],
            experience_years="5+",
            status=SessionStatus.QUESTIONS_GENERATED.value,
        )
        db_session.add(session)
        await db_session.flush()
        session_id = str(session.id)

        # Mock session service
        with patch(
            "backend.services.interview_service.session_service.get_session_meta",
            new_callable=AsyncMock,
            return_value={
                "session_id": session_id,
                "candidate_name": "Alice Developer",
                "skills": ["python"],
                "experience": "5+",
                "resume_text": SAMPLE_RESUME_TEXT,
            },
        ), patch(
            "backend.services.interview_service.session_service.get_questions_cache",
            new_callable=AsyncMock,
            return_value=mock_questions_cache,
        ), patch(
            "backend.services.interview_service.session_service.save_interview_state",
            new_callable=AsyncMock,
        ), patch(
            "backend.services.interview_service.session_service.clear_feedback",
            new_callable=AsyncMock,
        ), patch(
            "backend.services.interview_service.InterviewAgent.create_new",
            new_callable=AsyncMock,
        ) as mock_agent_create:
            # Setup mock agent
            mock_agent = MagicMock()
            mock_agent.state = MagicMock()
            mock_agent.state.conversation_history = []
            mock_agent.save = AsyncMock()
            mock_agent_create.return_value = mock_agent

            response = await client.post(
                f"/api/v1/interview/start/{session_id}",
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Hello" in data["message"] or "Alice" in data["message"]
        assert data["is_interview_complete"] is False
        assert data["current_question_number"] == 1
        assert data["total_questions"] == 3

    @pytest.mark.asyncio
    async def test_chat_answer_submission(
        self, client: AsyncClient, candidate_user, db_session,
        mock_redis, mock_questions_cache
    ):
        """Should submit an answer via chat and get feedback + next question."""
        headers = make_auth_header(candidate_user)

        # Create session
        from backend.models.interview import InterviewSession, SessionStatus
        from backend.models.schemas import ChatResponse

        session = InterviewSession(
            candidate_name="Alice Developer",
            user_id=candidate_user.id,
            resume_text=SAMPLE_RESUME_TEXT,
            skills_detected=["python"],
            experience_years="5+",
            status=SessionStatus.IN_PROGRESS.value,
        )
        db_session.add(session)
        await db_session.flush()
        session_id = str(session.id)

        mock_response = ChatResponse(
            success=True,
            session_id=session_id,
            message="Good answer! Next: Explain Docker.",
            feedback=None,
            is_interview_complete=False,
            current_question_number=2,
            total_questions=3,
        )

        with patch(
            "backend.routes.interview_routes.process_interview_message",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = await client.post(
                "/api/v1/interview/chat",
                json={
                    "session_id": session_id,
                    "message": "A list is mutable and a tuple is immutable in Python.",
                },
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["is_interview_complete"] is False
        assert "Docker" in data["message"]

    @pytest.mark.asyncio
    async def test_get_summary_after_completion(
        self, client: AsyncClient, candidate_user, db_session, mock_redis
    ):
        """Should return final summary after interview completes."""
        headers = make_auth_header(candidate_user)

        from backend.models.interview import InterviewSession, SessionStatus

        session = InterviewSession(
            candidate_name="Alice Developer",
            user_id=candidate_user.id,
            resume_text=SAMPLE_RESUME_TEXT,
            skills_detected=["python"],
            experience_years="5+",
            status=SessionStatus.COMPLETED.value,
            average_score=7.5,
            recommendation="Hire",
        )
        db_session.add(session)
        await db_session.flush()
        session_id = str(session.id)

        mock_summary = {
            "success": True,
            "session_id": session_id,
            "overall_score": "7.5/10",
            "performance_level": "Good — Strong Performance",
            "summary": "Good performance across 3 questions.",
            "recommendation": "Hire",
        }

        with patch(
            "backend.routes.interview_routes.generate_final_summary",
            new_callable=AsyncMock,
            return_value=mock_summary,
        ):
            response = await client.get(
                f"/api/v1/interview/summary/{session_id}",
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "7.5" in data["overall_score"]
        assert data["recommendation"] == "Hire"


# ══════════════════════════════════════════════════════════════════════════════
# SESSION CLEANUP
# ══════════════════════════════════════════════════════════════════════════════


class TestSessionCleanup:
    """Tests for Redis session cleanup."""

    @pytest.mark.asyncio
    async def test_delete_session_cache_removes_all_keys(self):
        """delete_session_cache should remove all session-related keys."""
        from backend.services.session_service import (
            save_session_meta,
            save_questions_cache,
            save_interview_state,
            save_parsed_resume,
            delete_session_cache,
            get_session_meta,
            get_questions_cache,
            get_interview_state,
            get_parsed_resume,
        )

        session_id = str(uuid.uuid4())

        # Mock all Redis calls
        store = {}

        async def mock_set(key, value, **kwargs):
            store[key] = value

        async def mock_get(key):
            return store.get(key)

        async def mock_delete(key):
            store.pop(key, None)

        with patch("backend.services.session_service.redis_set_json", side_effect=mock_set), \
             patch("backend.services.session_service.redis_get_json", side_effect=mock_get), \
             patch("backend.services.session_service.redis_set_pickle", side_effect=mock_set), \
             patch("backend.services.session_service.redis_get_pickle", side_effect=mock_get), \
             patch("backend.services.session_service.redis_set_bytes", side_effect=mock_set), \
             patch("backend.services.session_service.redis_get_bytes", side_effect=mock_get), \
             patch("backend.services.session_service.redis_delete", side_effect=mock_delete):

            # Save various session data
            await save_session_meta(
                session_id, "Alice", ["python"], "5+", "resume text"
            )
            await save_questions_cache(session_id, [{"q": "test?"}])
            await save_interview_state(session_id, {"index": 2})
            await save_parsed_resume(session_id, {"skills": ["python"]})

            # Verify data exists
            assert await get_session_meta(session_id) is not None
            assert await get_questions_cache(session_id) is not None

            # Delete all
            await delete_session_cache(session_id)

            # Verify all removed
            assert await get_session_meta(session_id) is None
            assert await get_questions_cache(session_id) is None
            assert await get_interview_state(session_id) is None
            assert await get_parsed_resume(session_id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session_does_not_crash(self):
        """Deleting a non-existent session should not raise errors."""
        from backend.services.session_service import delete_session_cache

        with patch("backend.services.session_service.redis_delete", new_callable=AsyncMock):
            # Should not raise
            await delete_session_cache("nonexistent-session-id")


# ══════════════════════════════════════════════════════════════════════════════
# REDIS STATE CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════


class TestRedisStateConsistency:
    """Tests for Redis state management consistency."""

    @pytest.mark.asyncio
    async def test_session_meta_roundtrip(self):
        """save → get session meta should preserve data."""
        from backend.services.session_service import save_session_meta, get_session_meta

        session_id = str(uuid.uuid4())
        store = {}

        async def mock_set(key, value, **kwargs):
            store[key] = value

        async def mock_get(key):
            return store.get(key)

        with patch("backend.services.session_service.redis_set_json", side_effect=mock_set), \
             patch("backend.services.session_service.redis_get_json", side_effect=mock_get):

            await save_session_meta(
                session_id, "Bob Smith", ["react", "typescript"], "3 years", "Full resume..."
            )
            result = await get_session_meta(session_id)

        assert result["session_id"] == session_id
        assert result["candidate_name"] == "Bob Smith"
        assert "react" in result["skills"]
        assert "typescript" in result["skills"]
        assert result["experience"] == "3 years"
        assert result["resume_text"] == "Full resume..."

    @pytest.mark.asyncio
    async def test_questions_cache_roundtrip(self):
        """save → get questions cache should preserve all questions."""
        from backend.services.session_service import save_questions_cache, get_questions_cache

        session_id = str(uuid.uuid4())
        store = {}

        async def mock_set(key, value, **kwargs):
            store[key] = value

        async def mock_get(key):
            return store.get(key)

        questions = [
            {"id": 1, "question": "Q1?", "keywords": ["k1"]},
            {"id": 2, "question": "Q2?", "keywords": ["k2"]},
        ]

        with patch("backend.services.session_service.redis_set_json", side_effect=mock_set), \
             patch("backend.services.session_service.redis_get_json", side_effect=mock_get):

            await save_questions_cache(session_id, questions)
            result = await get_questions_cache(session_id)

        assert len(result) == 2
        assert result[0]["question"] == "Q1?"
        assert result[1]["question"] == "Q2?"

    @pytest.mark.asyncio
    async def test_interview_state_roundtrip(self):
        """save → get interview state should track progress."""
        from backend.services.session_service import save_interview_state, get_interview_state

        session_id = str(uuid.uuid4())
        store = {}

        async def mock_set(key, value, **kwargs):
            store[key] = value

        async def mock_get(key):
            return store.get(key)

        with patch("backend.services.session_service.redis_set_json", side_effect=mock_set), \
             patch("backend.services.session_service.redis_get_json", side_effect=mock_get):

            # Save initial state
            await save_interview_state(session_id, {
                "current_question_index": 0,
                "total_questions": 10,
            })
            state = await get_interview_state(session_id)
            assert state["current_question_index"] == 0
            assert state["total_questions"] == 10

            # Update state (simulating progression)
            await save_interview_state(session_id, {
                "current_question_index": 5,
                "total_questions": 10,
            })
            state = await get_interview_state(session_id)
            assert state["current_question_index"] == 5

    @pytest.mark.asyncio
    async def test_feedback_accumulation(self):
        """add_answer_feedback should accumulate entries over time."""
        from backend.services.session_service import (
            add_answer_feedback,
            get_all_feedback,
            clear_feedback,
        )

        session_id = str(uuid.uuid4())
        store = {}

        async def mock_set(key, value, **kwargs):
            store[key] = value

        async def mock_get(key):
            return store.get(key)

        async def mock_delete(key):
            store.pop(key, None)

        with patch("backend.services.session_service.redis_set_json", side_effect=mock_set), \
             patch("backend.services.session_service.redis_get_json", side_effect=mock_get), \
             patch("backend.services.session_service.redis_delete", side_effect=mock_delete):

            # Add feedback entries one by one
            await add_answer_feedback(session_id, {"question": "Q1", "score": 7})
            await add_answer_feedback(session_id, {"question": "Q2", "score": 8})
            await add_answer_feedback(session_id, {"question": "Q3", "score": 5})

            # Should have all 3
            feedback = await get_all_feedback(session_id)
            assert len(feedback) == 3
            assert feedback[0]["score"] == 7
            assert feedback[2]["score"] == 5

            # Clear and verify
            await clear_feedback(session_id)
            feedback = await get_all_feedback(session_id)
            assert len(feedback) == 0

    @pytest.mark.asyncio
    async def test_parsed_resume_roundtrip(self):
        """save → get parsed resume data should preserve structure."""
        from backend.services.session_service import save_parsed_resume, get_parsed_resume

        session_id = str(uuid.uuid4())
        store = {}

        async def mock_set(key, value, **kwargs):
            store[key] = value

        async def mock_get(key):
            return store.get(key)

        parsed = {
            "skills": ["python", "react", "docker"],
            "experience_years": 5.0,
            "skill_categories": {"python": ["python"], "react": ["react"]},
            "education": ["B.Tech CS"],
        }

        with patch("backend.services.session_service.redis_set_json", side_effect=mock_set), \
             patch("backend.services.session_service.redis_get_json", side_effect=mock_get):

            await save_parsed_resume(session_id, parsed)
            result = await get_parsed_resume(session_id)

        assert result["skills"] == ["python", "react", "docker"]
        assert result["experience_years"] == 5.0
        assert "python" in result["skill_categories"]


# ══════════════════════════════════════════════════════════════════════════════
# ERROR CASES — LIFECYCLE VIOLATIONS
# ══════════════════════════════════════════════════════════════════════════════


class TestLifecycleErrorCases:
    """Tests for attempting operations out of order."""

    @pytest.mark.asyncio
    async def test_generate_questions_without_resume(
        self, client: AsyncClient, candidate_user, db_session, mock_redis
    ):
        """Generating questions for non-existent session should fail."""
        headers = make_auth_header(candidate_user)
        fake_session_id = str(uuid.uuid4())

        response = await client.post(
            f"/api/v1/interview/generate-questions/{fake_session_id}",
            headers=headers,
        )
        # Should get 404 (session not found) or 500
        assert response.status_code in (404, 500)

    @pytest.mark.asyncio
    async def test_start_interview_without_questions(
        self, client: AsyncClient, candidate_user, db_session, mock_redis
    ):
        """Starting interview without generated questions should fail."""
        headers = make_auth_header(candidate_user)

        from backend.models.interview import InterviewSession, SessionStatus

        session = InterviewSession(
            candidate_name="Alice",
            user_id=candidate_user.id,
            resume_text="resume",
            skills_detected=["python"],
            status=SessionStatus.CREATED.value,
        )
        db_session.add(session)
        await db_session.flush()
        session_id = str(session.id)

        # No questions cache in Redis
        with patch(
            "backend.services.interview_service.session_service.get_session_meta",
            new_callable=AsyncMock,
            return_value={"candidate_name": "Alice"},
        ), patch(
            "backend.services.interview_service.session_service.get_questions_cache",
            new_callable=AsyncMock,
            return_value=None,  # No questions!
        ):
            response = await client.post(
                f"/api/v1/interview/start/{session_id}",
                headers=headers,
            )

        # Should fail with 404 (ValueError) or 500
        assert response.status_code in (404, 500)

    @pytest.mark.asyncio
    async def test_chat_with_nonexistent_session(
        self, client: AsyncClient, candidate_user, db_session, mock_redis
    ):
        """Chatting with a non-existent session should fail."""
        headers = make_auth_header(candidate_user)
        fake_session_id = str(uuid.uuid4())

        # Create a session so ownership check passes
        from backend.models.interview import InterviewSession, SessionStatus

        session = InterviewSession(
            id=uuid.UUID(fake_session_id),
            candidate_name="Alice",
            user_id=candidate_user.id,
            resume_text="resume",
            skills_detected=["python"],
            status=SessionStatus.IN_PROGRESS.value,
        )
        db_session.add(session)
        await db_session.flush()

        # But no agent in Redis
        with patch(
            "backend.services.interview_service.InterviewAgent.restore",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await client.post(
                "/api/v1/interview/chat",
                json={
                    "session_id": fake_session_id,
                    "message": "My answer to the question",
                },
                headers=headers,
            )

        assert response.status_code in (404, 500)

    @pytest.mark.asyncio
    async def test_empty_answer_rejected(
        self, client: AsyncClient, candidate_user, mock_redis
    ):
        """Empty string answer should be rejected with 400."""
        headers = make_auth_header(candidate_user)

        response = await client.post(
            "/api/v1/interview/chat",
            json={
                "session_id": str(uuid.uuid4()),
                "message": "",
            },
            headers=headers,
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_whitespace_only_answer_rejected(
        self, client: AsyncClient, candidate_user, mock_redis
    ):
        """Whitespace-only answer should be rejected with 400."""
        headers = make_auth_header(candidate_user)

        response = await client.post(
            "/api/v1/interview/chat",
            json={
                "session_id": str(uuid.uuid4()),
                "message": "   \n\t   ",
            },
            headers=headers,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_session_id_format(
        self, client: AsyncClient, candidate_user, mock_redis
    ):
        """Non-UUID session_id should return 400."""
        headers = make_auth_header(candidate_user)

        response = await client.post(
            "/api/v1/interview/generate-questions/not-a-valid-uuid",
            headers=headers,
        )
        assert response.status_code == 400
        assert "uuid" in response.json()["detail"].lower()


# ══════════════════════════════════════════════════════════════════════════════
# SESSION OWNERSHIP ENFORCEMENT
# ══════════════════════════════════════════════════════════════════════════════


class TestSessionOwnership:
    """Tests that users can only access their own sessions."""

    @pytest.mark.asyncio
    async def test_candidate_cannot_access_other_users_session(
        self, client: AsyncClient, candidate_user, db_session, mock_redis
    ):
        """A candidate should not be able to access another user's session."""
        headers = make_auth_header(candidate_user)

        from backend.models.interview import InterviewSession, SessionStatus

        # Create session owned by a different user
        other_user_id = uuid.uuid4()
        session = InterviewSession(
            candidate_name="Other User",
            user_id=other_user_id,  # Different user!
            resume_text="resume",
            skills_detected=["java"],
            status=SessionStatus.IN_PROGRESS.value,
        )
        db_session.add(session)
        await db_session.flush()
        session_id = str(session.id)

        response = await client.post(
            f"/api/v1/interview/generate-questions/{session_id}",
            headers=headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_access_any_session(
        self, client: AsyncClient, admin_user, db_session, mock_redis
    ):
        """Admin users should be able to access any session."""
        headers = make_auth_header(admin_user)

        from backend.models.interview import InterviewSession, SessionStatus

        other_user_id = uuid.uuid4()
        session = InterviewSession(
            candidate_name="Any Candidate",
            user_id=other_user_id,
            resume_text="resume",
            skills_detected=["python"],
            status=SessionStatus.COMPLETED.value,
            average_score=7.0,
        )
        db_session.add(session)
        await db_session.flush()
        session_id = str(session.id)

        # Admin accessing summary of another user's session
        with patch(
            "backend.routes.interview_routes.generate_final_summary",
            new_callable=AsyncMock,
            return_value={"success": True, "session_id": session_id, "overall_score": "7.0/10"},
        ):
            response = await client.get(
                f"/api/v1/interview/summary/{session_id}",
                headers=headers,
            )

        # Admin should get 200, not 403
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_recruiter_can_access_any_session(
        self, client: AsyncClient, recruiter_user, db_session, mock_redis
    ):
        """Recruiter users should be able to access any session for review."""
        headers = make_auth_header(recruiter_user)

        from backend.models.interview import InterviewSession, SessionStatus

        other_user_id = uuid.uuid4()
        session = InterviewSession(
            candidate_name="Candidate X",
            user_id=other_user_id,
            resume_text="resume",
            skills_detected=["react"],
            status=SessionStatus.COMPLETED.value,
            average_score=8.0,
        )
        db_session.add(session)
        await db_session.flush()
        session_id = str(session.id)

        with patch(
            "backend.routes.interview_routes.generate_final_summary",
            new_callable=AsyncMock,
            return_value={"success": True, "session_id": session_id, "overall_score": "8.0/10"},
        ):
            response = await client.get(
                f"/api/v1/interview/summary/{session_id}",
                headers=headers,
            )

        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# INTERVIEW SERVICE UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestInterviewServiceUnit:
    """Unit tests for interview_service.py functions."""

    @pytest.mark.asyncio
    async def test_start_interview_creates_agent(self, db_session, mock_redis):
        """start_interview should create an InterviewAgent and return greeting."""
        from backend.services.interview_service import start_interview
        from backend.models.interview import InterviewSession, SessionStatus

        session = InterviewSession(
            candidate_name="Test User",
            user_id=uuid.uuid4(),
            resume_text="resume text",
            skills_detected=["python"],
            status=SessionStatus.QUESTIONS_GENERATED.value,
        )
        db_session.add(session)
        await db_session.flush()
        session_id = str(session.id)

        questions_cache = [
            {"id": 1, "question": "What is Python?", "type": "technical",
             "category": "python", "difficulty": "easy", "expected_keywords": ["python"]},
        ]

        with patch(
            "backend.services.interview_service.session_service.get_session_meta",
            new_callable=AsyncMock,
            return_value={"candidate_name": "Test User"},
        ), patch(
            "backend.services.interview_service.session_service.get_questions_cache",
            new_callable=AsyncMock,
            return_value=questions_cache,
        ), patch(
            "backend.services.interview_service.session_service.save_interview_state",
            new_callable=AsyncMock,
        ), patch(
            "backend.services.interview_service.session_service.clear_feedback",
            new_callable=AsyncMock,
        ), patch(
            "backend.services.interview_service.InterviewAgent.create_new",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_agent = MagicMock()
            mock_agent.state = MagicMock()
            mock_agent.state.conversation_history = []
            mock_agent.save = AsyncMock()
            mock_create.return_value = mock_agent

            response = await start_interview(session_id, db_session)

        assert response.success is True
        assert "Test User" in response.message
        assert response.is_interview_complete is False
        assert response.total_questions == 1
        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_interview_no_session_meta_raises(self, db_session, mock_redis):
        """start_interview should raise ValueError if session meta not found."""
        from backend.services.interview_service import start_interview
        from backend.models.interview import InterviewSession

        session = InterviewSession(
            candidate_name="X",
            user_id=uuid.uuid4(),
            resume_text="r",
            skills_detected=[],
        )
        db_session.add(session)
        await db_session.flush()

        with patch(
            "backend.services.interview_service.session_service.get_session_meta",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(ValueError, match="not found"):
                await start_interview(str(session.id), db_session)

    @pytest.mark.asyncio
    async def test_process_message_no_agent_raises(self, db_session, mock_redis):
        """process_interview_message should raise if no agent is restored."""
        from backend.services.interview_service import process_interview_message

        with patch(
            "backend.services.interview_service.InterviewAgent.restore",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(ValueError, match="No active interview"):
                await process_interview_message("fake-id", "answer", db_session)
