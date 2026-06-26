"""
Project Extractor — Extracts structured project JSON from resume text.

Uses an LLM chain to parse free-form resume text into actionable
project data: name, role, tech stack, challenges, solutions, outcomes.

This structured output feeds the Context-Aware Question Generation Engine,
ensuring questions are always grounded in the candidate's real experience.
"""

import json
import re
from typing import Optional

from langchain_openai import ChatOpenAI

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.models.schemas import ProjectContext, ProjectDetail
from backend.services.prompt_templates import PROJECT_EXTRACTION_PROMPT

logger = get_logger("backend.services.project_extractor")


def _clean_json_response(raw: str) -> str:
    """
    Strip markdown fences and other noise from an LLM's JSON response.

    Args:
        raw: Raw LLM output that may contain ```json ... ``` wrappers

    Returns:
        Cleaned string ready for json.loads()
    """
    cleaned = raw.strip()
    # Remove markdown code fences
    cleaned = re.sub(r"```json\s*", "", cleaned)
    cleaned = re.sub(r"```\s*", "", cleaned)
    # Remove any leading/trailing whitespace again
    return cleaned.strip()


def _build_fallback_context(
    resume_text: str,
    skills: list,
    experience: str,
) -> ProjectContext:
    """
    Build a minimal ProjectContext when LLM extraction fails.
    Falls back to a single generic project derived from detected skills.

    Args:
        resume_text: Raw resume text
        skills: Previously detected skills list
        experience: Experience years string

    Returns:
        A minimal ProjectContext
    """
    # Determine experience level from the string
    exp_level = "mid"
    if experience and experience != "Not specified":
        try:
            years = int(re.search(r"\d+", experience).group())
            if years <= 2:
                exp_level = "junior"
            elif years >= 5:
                exp_level = "senior"
        except (AttributeError, ValueError):
            pass

    return ProjectContext(
        projects=[
            ProjectDetail(
                name="Primary Project",
                role="Developer",
                tech_stack=skills[:8] if skills else ["Python"],
                challenge="Building and delivering a production application",
                solution="Implemented using modern frameworks and best practices",
                outcome="Successfully deployed application",
            )
        ],
        primary_skills=skills[:5] if skills else ["Python"],
        experience_level=exp_level,
        domain_expertise=["Software Engineering"],
    )


async def extract_projects(
    resume_text: str,
    skills: list | None = None,
    experience: str = "Not specified",
) -> ProjectContext:
    """
    Extract structured project data from resume text using an LLM.

    Process:
    1. Send resume text to OpenAI with the extraction prompt
    2. Parse the JSON response into a ProjectContext
    3. Validate and enrich the output
    4. Fall back to skill-based context if extraction fails

    Args:
        resume_text: Full text extracted from the resume PDF
        skills: Pre-detected skills (used as fallback enrichment)
        experience: Experience years string

    Returns:
        ProjectContext with structured project data
    """
    skills = skills or []

    logger.info(
        "extracting_projects",
        resume_length=len(resume_text),
        pre_detected_skills=len(skills),
    )

    try:
        # Initialize the LLM
        llm = ChatOpenAI(
            model=settings.OPENROUTER_MODEL,
            temperature=0.2,  # Low temperature for factual extraction
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": settings.OPENROUTER_SITE_URL,
                "X-OpenRouter-Title": settings.OPENROUTER_SITE_NAME,
            },
        )

        # Build the prompt
        prompt = PROJECT_EXTRACTION_PROMPT.format(
            resume_text=resume_text[:6000],  # Cap to avoid token limits
        )

        # Call the LLM
        raw_response = llm.predict(prompt)
        cleaned = _clean_json_response(raw_response)
        data = json.loads(cleaned)

        logger.info(
            "projects_extracted_raw",
            num_projects=len(data.get("projects", [])),
            primary_skills=data.get("primary_skills", []),
        )

        # Parse into Pydantic models
        projects = []
        for proj in data.get("projects", []):
            projects.append(ProjectDetail(
                name=proj.get("name", "Unnamed Project"),
                role=proj.get("role", "Developer"),
                tech_stack=proj.get("tech_stack", []),
                challenge=proj.get("challenge", ""),
                solution=proj.get("solution", ""),
                outcome=proj.get("outcome", ""),
            ))

        # Ensure at least one project
        if not projects:
            logger.warning("no_projects_extracted_using_fallback")
            return _build_fallback_context(resume_text, skills, experience)

        # Determine experience level
        exp_level = data.get("experience_level", "mid")
        if exp_level not in ("junior", "mid", "senior"):
            exp_level = "mid"

        context = ProjectContext(
            projects=projects[:6],  # Cap at 6 projects
            primary_skills=data.get("primary_skills", skills)[:10],
            experience_level=exp_level,
            domain_expertise=data.get("domain_expertise", ["Software Engineering"]),
        )

        logger.info(
            "project_context_built",
            num_projects=len(context.projects),
            experience_level=context.experience_level,
            domains=context.domain_expertise,
        )

        return context

    except json.JSONDecodeError as e:
        logger.error("project_extraction_json_parse_failed", error=str(e))
        return _build_fallback_context(resume_text, skills, experience)

    except Exception as e:
        logger.error("project_extraction_failed", error=str(e), error_type=type(e).__name__)
        return _build_fallback_context(resume_text, skills, experience)
