"""
LeetCode Integration Routes — Search and import problems from LeetCode.

These routes allow the frontend to:
1. Search LeetCode problems by keyword, difficulty, or tags
2. Fetch full problem details (description + example test cases)
3. Import a LeetCode problem as a local coding challenge
4. Get the daily LeetCode challenge

The existing sandbox execution and scoring logic is NOT changed.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.session import get_db
from backend.models.coding_challenge import CodingChallenge
from backend.services.leetcode_service import leetcode_service
from backend.core.security import get_current_active_user
from backend.core.logging import get_logger

logger = get_logger("backend.routes.leetcode_routes")

router = APIRouter(
    prefix="/leetcode",
    tags=["LeetCode Integration"],
    dependencies=[Depends(get_current_active_user)],
)


# ── Request/Response Schemas ───────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = ""
    difficulty: Optional[str] = None  # "EASY", "MEDIUM", "HARD"
    tags: Optional[List[str]] = None  # ["array", "hash-table", "dynamic-programming"]
    limit: int = 20
    skip: int = 0
    number: Optional[int] = None  # Search by LeetCode problem number (e.g., 1, 121, 200)


class ImportRequest(BaseModel):
    title_slug: str
    custom_test_cases: Optional[List[dict]] = None  # Override test cases if needed


class TestCaseOverride(BaseModel):
    """For manually specifying test cases when importing."""
    input: str
    expected_output: str
    is_hidden: bool = False


# ── Route Handlers ─────────────────────────────────────────────────────────

@router.post("/search")
async def search_leetcode_problems(request: SearchRequest):
    """
    Search LeetCode problems.
    
    Supports filtering by:
    - query: keyword search in problem title
    - difficulty: EASY, MEDIUM, HARD
    - tags: array, hash-table, dynamic-programming, tree, etc.
    - limit/skip: pagination
    - number: search by problem number (e.g., 1 for Two Sum)
    """
    # If number is provided, use it as the query
    search_query = str(request.number) if request.number else request.query

    result = await leetcode_service.search_problems(
        query=search_query,
        difficulty=request.difficulty,
        tags=request.tags,
        limit=request.limit,
        skip=request.skip,
    )
    return result


@router.get("/problem/{title_slug}")
async def get_leetcode_problem(title_slug: str):
    """
    Fetch full details of a specific LeetCode problem.
    
    Returns description, example test cases, hints, and topic tags.
    """
    result = await leetcode_service.fetch_problem(title_slug)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Problem not found"))
    return result


@router.get("/daily")
async def get_daily_problem():
    """
    Get today's LeetCode Daily Challenge.
    
    Returns the problem with description and example test cases.
    """
    result = await leetcode_service.fetch_daily_problem()
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "Could not fetch daily problem"))
    return result


@router.post("/import")
async def import_leetcode_problem(
    request: ImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Import a LeetCode problem as a local coding challenge.
    
    This adds the problem to the coding_challenges table so it
    can be used in interview sessions with the existing sandbox.
    
    If the problem is already imported (by title_slug), returns the existing one.
    """
    # Check if already imported
    title_prefix = f"[LC] "
    result = await db.execute(
        select(CodingChallenge).where(
            CodingChallenge.title.like(f"{title_prefix}%")
        )
    )
    existing = result.scalars().all()
    for ex in existing:
        # Check by slug in description or title match
        if request.title_slug in (ex.description or ""):
            return {
                "success": True,
                "action": "already_exists",
                "challenge_id": str(ex.id),
                "title": ex.title,
            }

    # Fetch from LeetCode
    fetch_result = await leetcode_service.fetch_problem(request.title_slug)
    if not fetch_result.get("success"):
        raise HTTPException(
            status_code=502,
            detail=fetch_result.get("error", "Failed to fetch problem from LeetCode")
        )

    problem = fetch_result["problem"]

    # Convert to local format
    challenge_data = leetcode_service.convert_to_challenge_format(
        problem,
        custom_test_cases=request.custom_test_cases,
    )

    # Add source reference to description
    description_with_source = (
        f"{challenge_data['description']}\n\n"
        f"---\n"
        f"**Source:** [LeetCode #{problem.get('questionId', '')} — {problem.get('title', '')}]"
        f"({problem.get('link', '')})\n"
        f"**Tags:** {', '.join(problem.get('topicTags', []))}\n"
        f"**Slug:** `{request.title_slug}`"
    )

    # Create the challenge
    new_challenge = CodingChallenge(
        title=challenge_data["title"],
        description=description_with_source,
        difficulty=challenge_data["difficulty"],
        template_code=challenge_data["template_code"],
        test_cases=challenge_data["test_cases"],
        time_limit=challenge_data["time_limit"],
        memory_limit=challenge_data["memory_limit"],
    )

    db.add(new_challenge)
    await db.commit()
    await db.refresh(new_challenge)

    logger.info(
        "leetcode_problem_imported",
        slug=request.title_slug,
        challenge_id=str(new_challenge.id),
        test_cases_count=len(challenge_data["test_cases"]),
    )

    return {
        "success": True,
        "action": "imported",
        "challenge_id": str(new_challenge.id),
        "title": new_challenge.title,
        "difficulty": new_challenge.difficulty,
        "test_cases_count": len(challenge_data["test_cases"]),
        "needs_verification": any(
            tc.get("needs_verification") for tc in challenge_data["test_cases"]
        ),
    }


@router.get("/tags")
async def get_available_tags():
    """Return popular LeetCode topic tags for filtering."""
    return {
        "tags": [
            {"slug": "array", "name": "Array"},
            {"slug": "string", "name": "String"},
            {"slug": "hash-table", "name": "Hash Table"},
            {"slug": "dynamic-programming", "name": "Dynamic Programming"},
            {"slug": "math", "name": "Math"},
            {"slug": "sorting", "name": "Sorting"},
            {"slug": "greedy", "name": "Greedy"},
            {"slug": "depth-first-search", "name": "Depth-First Search"},
            {"slug": "binary-search", "name": "Binary Search"},
            {"slug": "breadth-first-search", "name": "Breadth-First Search"},
            {"slug": "tree", "name": "Tree"},
            {"slug": "matrix", "name": "Matrix"},
            {"slug": "two-pointers", "name": "Two Pointers"},
            {"slug": "binary-tree", "name": "Binary Tree"},
            {"slug": "bit-manipulation", "name": "Bit Manipulation"},
            {"slug": "stack", "name": "Stack"},
            {"slug": "heap-priority-queue", "name": "Heap (Priority Queue)"},
            {"slug": "graph", "name": "Graph"},
            {"slug": "linked-list", "name": "Linked List"},
            {"slug": "recursion", "name": "Recursion"},
            {"slug": "sliding-window", "name": "Sliding Window"},
            {"slug": "backtracking", "name": "Backtracking"},
            {"slug": "divide-and-conquer", "name": "Divide and Conquer"},
            {"slug": "trie", "name": "Trie"},
            {"slug": "union-find", "name": "Union Find"},
        ]
    }
