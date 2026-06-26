"""
Context-Aware Question Generation Engine — The brain of the system.

Orchestrates question generation across 4 specialized categories:
  • Project-Based  — Deep-dive into specific resume projects
  • Challenge      — Scenario/problem-solving from their actual experience
  • Architecture   — System design questions using their real stack
  • Debugging      — Realistic bug scenarios in their project context

Process:
1. Accept structured ProjectContext + FAISS vector store
2. Enrich context with embeddings-retrieved resume chunks
3. Run each category's prompt template through ChatOpenAI
4. Parse, validate, and deduplicate questions
5. Assign difficulty levels and enforce the anti-generic guard

Never generates:
  ✗ "What is Python?"
  ✗ "Explain OOP concepts"
  ✗ Generic definition questions

Always generates:
  ✓ "In your EcoTrack project, you used Redis for caching. How did you handle invalidation?"
  ✓ "Your AgriMind model showed accuracy drops. Walk me through debugging that."
"""

import json
import re
from typing import List, Optional

from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.models.schemas import (
    DifficultyLevel,
    InterviewQuestion,
    ProjectContext,
    QuestionCategory,
    QuestionType,
)
from backend.services.prompt_templates import (
    ANTI_GENERIC_GUARD,
    get_template,
    get_all_categories,
)
from backend.services.anti_repetition import AntiRepetitionEngine, create_engine

logger = get_logger("backend.services.context_engine")

# ── Question distribution per category ──────────────────────────────
DEFAULT_DISTRIBUTION = {
    "project_based": 2,
    "challenge": 2,
    "architecture": 2,
    "debugging": 1,
    "general": 3,
}


def _clean_json_response(raw: str) -> str:
    """Strip markdown fences and noise from LLM JSON output."""
    cleaned = raw.strip()
    cleaned = re.sub(r"```json\s*", "", cleaned)
    cleaned = re.sub(r"```\s*", "", cleaned)
    return cleaned.strip()


def _is_generic_question(question_text: str) -> bool:
    """
    Check if a question is a generic definition-style question.
    Returns True if the question should be REJECTED.

    Catches patterns like:
    - "What is Python?"
    - "Explain what Java is"
    - "Define machine learning"
    - "What are the features of React?"
    """
    text_lower = question_text.lower().strip()

    # Pattern 1: "What is <technology>?"
    if re.match(r"^what\s+is\s+\w+[\w\s]*\??$", text_lower):
        return True

    # Pattern 2: "Define <concept>"
    if re.match(r"^define\s+", text_lower):
        return True

    # Pattern 3: "Explain what <X> is"
    if re.match(r"^explain\s+what\s+\w+\s+is", text_lower):
        return True

    # Pattern 4: "What are the features/advantages/benefits of <X>?"
    if re.match(r"^what\s+are\s+the\s+(features|advantages|benefits|disadvantages)\s+of\s+", text_lower):
        return True

    # Pattern 5: "List the types of <X>"
    if re.match(r"^list\s+the\s+(types|kinds|forms)\s+of\s+", text_lower):
        return True

    # Pattern 6: "Can you explain <X>?" (too generic without project context)
    if re.match(r"^can\s+you\s+explain\s+\w+\??$", text_lower):
        return True

    return False


def _format_projects_json(context: ProjectContext) -> str:
    """
    Format projects into a readable JSON string for prompt injection.

    Args:
        context: The structured project context

    Returns:
        Pretty-printed JSON string of projects
    """
    projects_data = []
    for proj in context.projects:
        projects_data.append({
            "name": proj.name,
            "role": proj.role,
            "tech_stack": proj.tech_stack,
            "challenge": proj.challenge,
            "solution": proj.solution,
            "outcome": proj.outcome,
        })
    return json.dumps(projects_data, indent=2)


def _get_resume_context_from_vectorstore(
    vector_store,
    context: ProjectContext,
) -> str:
    """
    Query the FAISS vector store for relevant resume chunks
    using the project tech stacks as queries.

    Args:
        vector_store: FAISS vector store with resume embeddings
        context: Structured project context

    Returns:
        Concatenated relevant resume text chunks
    """
    if vector_store is None:
        return ""

    try:
        # Build search queries from project details
        queries = []
        for proj in context.projects:
            queries.append(f"{proj.name} {proj.challenge} {' '.join(proj.tech_stack[:5])}")

        # Also search for primary skills
        if context.primary_skills:
            queries.append(" ".join(context.primary_skills[:5]))

        # Retrieve relevant chunks
        all_chunks = []
        seen_content = set()

        for query in queries[:4]:  # Limit to 4 queries
            try:
                docs = vector_store.similarity_search(query, k=3)
                for doc in docs:
                    content = doc.page_content.strip()
                    if content and content not in seen_content:
                        seen_content.add(content)
                        all_chunks.append(content)
            except Exception:
                continue

        return "\n\n".join(all_chunks[:8])  # Cap at 8 chunks

    except Exception as e:
        logger.warning("vectorstore_query_failed", error=str(e))
        return ""


def _parse_questions_from_json(
    raw_response: str,
    category: str,
    start_id: int,
) -> List[InterviewQuestion]:
    """
    Parse the LLM's JSON response into InterviewQuestion objects.
    Applies the anti-generic guard to reject surface-level questions.

    Args:
        raw_response: Raw JSON string from the LLM
        category: Question category (project_based, challenge, etc.)
        start_id: Starting ID for question numbering

    Returns:
        List of validated InterviewQuestion objects
    """
    try:
        cleaned = _clean_json_response(raw_response)
        questions_data = json.loads(cleaned)

        if not isinstance(questions_data, list):
            logger.warning("llm_returned_non_list", category=category)
            return []

        questions = []
        current_id = start_id

        for q_data in questions_data:
            question_text = q_data.get("question", "").strip()

            # Skip empty questions
            if not question_text:
                continue

            # Apply anti-generic guard
            if _is_generic_question(question_text):
                logger.info(
                    "rejected_generic_question",
                    question=question_text[:80],
                    category=category,
                )
                continue

            # Map difficulty
            diff_raw = q_data.get("difficulty", "medium").lower()
            try:
                difficulty = DifficultyLevel(diff_raw)
            except ValueError:
                difficulty = DifficultyLevel.MEDIUM

            # Map category
            try:
                q_category = QuestionCategory(category)
            except ValueError:
                q_category = QuestionCategory.PROJECT_BASED

            questions.append(InterviewQuestion(
                id=current_id,
                question=question_text,
                type=QuestionType.TECHNICAL,
                topic=q_data.get("topic", ""),
                category=q_category,
                difficulty=difficulty,
                project_reference=q_data.get("project_reference", ""),
            ))
            current_id += 1

        return questions

    except json.JSONDecodeError as e:
        logger.error(
            "question_json_parse_failed",
            category=category,
            error=str(e),
            raw_preview=raw_response[:200],
        )
        return []


async def generate_contextual_questions(
    context: ProjectContext,
    vector_store=None,
    distribution: dict | None = None,
    db: AsyncSession | None = None,
    session_id: str | None = None,
) -> List[InterviewQuestion]:
    """
    Generate context-aware interview questions across all 4 categories.

    This is the main entry point for the engine. It:
    1. Enriches context with FAISS-retrieved resume chunks
    2. Runs each category's specialized prompt template
    3. Parses, validates, and deduplicates questions via Anti-Repetition Engine
    4. Returns a combined, numbered list of questions

    Args:
        context: Structured ProjectContext from project_extractor
        vector_store: Optional FAISS vector store for resume enrichment
        distribution: Optional dict overriding question counts per category.
                      Default: {project_based: 4, challenge: 3, architecture: 3, debugging: 2}
        db: Optional async SQLAlchemy session (required for deduplication)
        session_id: Optional session ID (required for deduplication)

    Returns:
        List of InterviewQuestion objects (typically 12 total)
    """
    dist = distribution or DEFAULT_DISTRIBUTION

    logger.info(
        "starting_contextual_generation",
        num_projects=len(context.projects),
        experience_level=context.experience_level,
        distribution=dist,
    )

    # ── Initialize Anti-Repetition Engine (if DB + session available) ──
    dedup_engine: Optional[AntiRepetitionEngine] = None
    if db is not None and session_id is not None:
        try:
            dedup_engine = await create_engine(session_id, db)
            logger.info(
                "dedup_engine_initialized",
                session_id=session_id,
                existing_vectors=dedup_engine.index.ntotal,
            )
        except Exception as e:
            logger.warning(
                "dedup_engine_init_failed_continuing_without",
                error=str(e),
                error_type=type(e).__name__,
            )
            dedup_engine = None

    # Initialize the LLM
    llm = ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        temperature=0.7,  # Creative for varied questions
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": settings.OPENROUTER_SITE_URL,
            "X-OpenRouter-Title": settings.OPENROUTER_SITE_NAME,
        },
    )

    # Pre-compute shared context
    projects_json = _format_projects_json(context)
    resume_context = _get_resume_context_from_vectorstore(vector_store, context)
    primary_skills_str = ", ".join(context.primary_skills) or "General programming"
    domain_str = ", ".join(context.domain_expertise) or "Software Engineering"

    all_questions: List[InterviewQuestion] = []
    current_id = 1

    # Generate questions for each category
    for category in get_all_categories():
        num_questions = dist.get(category, 2)
        if num_questions <= 0:
            continue

        try:
            template = get_template(category)

            # Fill in the template
            prompt = template.format(
                anti_generic_guard=ANTI_GENERIC_GUARD,
                primary_skills=primary_skills_str,
                experience_level=context.experience_level,
                domain_expertise=domain_str,
                projects_json=projects_json,
                resume_context=resume_context or "(No additional context available)",
                num_questions=num_questions,
            )

            # Call the LLM
            logger.info("generating_category", category=category, num_questions=num_questions)
            response_msg = llm.invoke(prompt)
            raw_response = response_msg.content if hasattr(response_msg, "content") else str(response_msg)

            # Parse the response
            category_questions = _parse_questions_from_json(
                raw_response, category, current_id
            )

            # Take only the requested number
            category_questions = category_questions[:num_questions]

            # ── Anti-Repetition: deduplicate against all prior questions ──
            if dedup_engine is not None and category_questions:
                pre_dedup_count = len(category_questions)
                category_questions = await dedup_engine.deduplicate_batch(
                    category_questions, db
                )
                dedup_rejected = pre_dedup_count - len(category_questions)
                if dedup_rejected > 0:
                    logger.info(
                        "dedup_filtered_category",
                        category=category,
                        rejected=dedup_rejected,
                        kept=len(category_questions),
                    )

            logger.info(
                "category_generated",
                category=category,
                requested=num_questions,
                generated=len(category_questions),
            )

            all_questions.extend(category_questions)
            current_id += len(category_questions)

        except Exception as e:
            logger.error(
                "category_generation_failed",
                category=category,
                error=str(e),
                error_type=type(e).__name__,
            )
            # Continue with other categories — partial results are fine
            continue

    # Re-number all questions sequentially
    for i, q in enumerate(all_questions):
        q.id = i + 1

    # Fallback: if we got nothing at all, generate minimal questions
    if not all_questions:
        logger.warning("all_categories_failed_using_fallback")
        all_questions = _generate_fallback_questions(context)

    logger.info(
        "contextual_generation_complete",
        total_questions=len(all_questions),
        categories={cat: sum(1 for q in all_questions if q.category.value == cat)
                    for cat in get_all_categories()},
        dedup_enabled=dedup_engine is not None,
    )

    return all_questions


def _generate_fallback_questions(context: ProjectContext) -> List[InterviewQuestion]:
    """
    Emergency fallback when LLM generation fails entirely.
    Creates project-specific questions from the structured context
    WITHOUT calling the LLM.

    Args:
        context: Structured project context

    Returns:
        List of basic but project-specific questions
    """
    questions = []
    q_id = 1

    # Generate at least one question per project
    for proj in context.projects[:4]:
        tech_str = ", ".join(proj.tech_stack[:4]) if proj.tech_stack else "your tech stack"

        questions.append(InterviewQuestion(
            id=q_id,
            question=f"Walk me through the architecture of your {proj.name} project. "
                     f"Why did you choose {tech_str} for this specific use case?",
            type=QuestionType.TECHNICAL,
            topic=proj.tech_stack[0] if proj.tech_stack else "Architecture",
            category=QuestionCategory.PROJECT_BASED,
            difficulty=DifficultyLevel.MEDIUM,
            project_reference=proj.name,
        ))
        q_id += 1

        if proj.challenge:
            questions.append(InterviewQuestion(
                id=q_id,
                question=f"In your {proj.name} project, you mentioned the challenge of "
                         f"'{proj.challenge}'. How did you approach solving this, and "
                         f"what alternatives did you consider?",
                type=QuestionType.TECHNICAL,
                topic="Problem Solving",
                category=QuestionCategory.CHALLENGE,
                difficulty=DifficultyLevel.MEDIUM,
                project_reference=proj.name,
            ))
            q_id += 1

    # Add architecture question using primary skills
    if context.primary_skills:
        skills_str = ", ".join(context.primary_skills[:4])
        questions.append(InterviewQuestion(
            id=q_id,
            question=f"You've worked extensively with {skills_str}. "
                     f"If you were designing a system from scratch today, "
                     f"how would your architecture decisions differ from your past projects?",
            type=QuestionType.TECHNICAL,
            topic="System Design",
            category=QuestionCategory.ARCHITECTURE,
            difficulty=DifficultyLevel.HARD,
            project_reference="cross-project",
        ))
        q_id += 1

    # Ensure minimum of 4 questions
    while len(questions) < 4:
        questions.append(InterviewQuestion(
            id=q_id,
            question="Describe the most complex debugging scenario you've faced in a recent project. "
                     "Walk me through your systematic approach to isolating and fixing the issue.",
            type=QuestionType.TECHNICAL,
            topic="Debugging",
            category=QuestionCategory.DEBUGGING,
            difficulty=DifficultyLevel.MEDIUM,
            project_reference="cross-project",
        ))
        q_id += 1
        break  # Only add one debugging fallback

    return questions
