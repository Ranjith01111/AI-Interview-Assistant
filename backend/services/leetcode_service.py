"""
LeetCode Integration Service — Fetches problems from LeetCode GraphQL API.

FIXES (2026-06-29):
1. Uses LeetCode's official GraphQL API directly for full 3000+ problem access
2. Generates template code for ALL languages (Python, JavaScript, C++, Java, Go, etc.)
3. Supports search by problem NUMBER (e.g., "1" → Two Sum, "121" → Best Time to Buy Stock)

Fallback: alfa-leetcode-api if GraphQL is rate-limited.
"""

import re
import json
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from backend.core.logging import get_logger

logger = get_logger("backend.services.leetcode_service")

# ── Configuration ────────────────────────────────────────────────────────────
LEETCODE_API_BASE = "https://alfa-leetcode-api.onrender.com"
LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"

# Timeout for external API calls
REQUEST_TIMEOUT = 15.0


class LeetCodeService:
    """Fetches LeetCode problems, descriptions, and example test cases."""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Content-Type": "application/json",
                    "Referer": "https://leetcode.com",
                },
                follow_redirects=True,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── Search Problems (with number-based search) ───────────────────────────
    async def search_problems(
        self,
        query: str = "",
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """
        Search LeetCode problems via GraphQL API.

        Supports:
        - Keyword search in title (e.g., "two sum")
        - Number-based search (e.g., "1", "121", "200")
        - Difficulty filter: "EASY", "MEDIUM", "HARD"
        - Tag filter: ["array", "dynamic-programming"]
        - Pagination via limit/skip
        """
        # First try: search by number if query is a number
        if query.strip().isdigit():
            result = await self._fetch_by_number(int(query.strip()))
            if result and result.get("success"):
                return result

        # Use LeetCode GraphQL for full problem list
        try:
            result = await self._graphql_search(query, difficulty, tags, limit, skip)
            if result.get("success") and result.get("problems"):
                return result
        except Exception as e:
            logger.warning("graphql_search_failed_falling_back", error=str(e))

        # Fallback to alfa-leetcode-api
        return await self._alfa_api_search(query, difficulty, tags, limit, skip)

    # ── Fetch by Problem Number ──────────────────────────────────────────────
    async def _fetch_by_number(self, number: int) -> Optional[Dict[str, Any]]:
        """Fetch a specific problem by its LeetCode number (frontendQuestionId)."""
        try:
            # GraphQL query to get problem by number
            graphql_query = {
                "query": """
                    query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
                        problemsetQuestionList: questionList(
                            categorySlug: $categorySlug
                            limit: $limit
                            skip: $skip
                            filters: $filters
                        ) {
                            total: totalNum
                            questions: data {
                                frontendQuestionId: questionFrontendId
                                title
                                titleSlug
                                difficulty
                                topicTags { name slug }
                                isPaidOnly: paidOnly
                            }
                        }
                    }
                """,
                "variables": {
                    "categorySlug": "",
                    "skip": max(0, number - 5),
                    "limit": 10,
                    "filters": {}
                }
            }

            response = await self.client.post(LEETCODE_GRAPHQL_URL, json=graphql_query)
            response.raise_for_status()
            data = response.json()

            questions = data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])
            
            # Find exact match by number
            matched = []
            for q in questions:
                if str(q.get("frontendQuestionId", "")) == str(number):
                    matched.append({
                        "title": q["title"],
                        "titleSlug": q["titleSlug"],
                        "difficulty": q["difficulty"],
                        "topicTags": [t["name"] for t in (q.get("topicTags") or [])],
                        "isPaidOnly": q.get("isPaidOnly", False),
                        "questionId": str(q["frontendQuestionId"]),
                    })
                    break

            if matched:
                return {"success": True, "problems": matched, "total": 1, "source": "leetcode"}

            # If not found in range, try direct slug guess
            return None

        except Exception as e:
            logger.warning("fetch_by_number_failed", number=number, error=str(e))
            return None

    # ── GraphQL Search (Full 3000+ Problems) ─────────────────────────────────
    async def _graphql_search(
        self,
        query: str = "",
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Search using LeetCode's official GraphQL endpoint."""
        filters = {}
        if difficulty:
            filters["difficulty"] = difficulty.upper()
        if tags:
            filters["tags"] = tags
        if query and not query.strip().isdigit():
            filters["searchKeywords"] = query

        graphql_query = {
            "query": """
                query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
                    problemsetQuestionList: questionList(
                        categorySlug: $categorySlug
                        limit: $limit
                        skip: $skip
                        filters: $filters
                    ) {
                        total: totalNum
                        questions: data {
                            frontendQuestionId: questionFrontendId
                            title
                            titleSlug
                            difficulty
                            topicTags { name slug }
                            isPaidOnly: paidOnly
                            acRate
                        }
                    }
                }
            """,
            "variables": {
                "categorySlug": "",
                "skip": skip,
                "limit": limit,
                "filters": filters,
            }
        }

        response = await self.client.post(LEETCODE_GRAPHQL_URL, json=graphql_query)
        response.raise_for_status()
        data = response.json()

        question_list = data.get("data", {}).get("problemsetQuestionList", {})
        questions = question_list.get("questions", [])
        total = question_list.get("total", 0)

        problems = []
        for q in questions:
            problems.append({
                "title": q.get("title", ""),
                "titleSlug": q.get("titleSlug", ""),
                "difficulty": q.get("difficulty", "Medium"),
                "topicTags": [t["name"] for t in (q.get("topicTags") or [])],
                "isPaidOnly": q.get("isPaidOnly", False),
                "questionId": str(q.get("frontendQuestionId", "")),
                "acRate": round(q.get("acRate", 0), 1),
            })

        return {
            "success": True,
            "problems": problems,
            "total": total,
            "source": "leetcode",
        }

    # ── Alfa API Fallback Search ─────────────────────────────────────────────
    async def _alfa_api_search(
        self,
        query: str = "",
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Fallback search using alfa-leetcode-api."""
        try:
            params = {"limit": str(limit), "skip": str(skip)}
            if tags:
                params["tags"] = "+".join(tags)
            if difficulty:
                params["difficulty"] = difficulty.upper()

            url = f"{LEETCODE_API_BASE}/problems"
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            problems = []
            raw_problems = data if isinstance(data, list) else data.get("problemsetQuestionList", [])

            for p in raw_problems:
                title = p.get("title", "") or p.get("questionTitle", "")
                slug = p.get("titleSlug", "")
                diff = p.get("difficulty", "Medium")
                qid = str(p.get("frontendQuestionId", "") or p.get("questionFrontendId", ""))

                if query and query.lower() not in title.lower() and query.lower() not in slug.lower() and query != qid:
                    continue

                problems.append({
                    "title": title,
                    "titleSlug": slug,
                    "difficulty": diff,
                    "topicTags": [t.get("name", "") for t in (p.get("topicTags", []) or [])],
                    "isPaidOnly": p.get("isPaidOnly", False),
                    "questionId": qid,
                })

            return {"success": True, "problems": problems[:limit], "total": len(problems), "source": "leetcode"}
        except Exception as e:
            logger.error("alfa_api_search_failed", error=str(e))
            return {"success": False, "error": str(e), "problems": []}

    # ── Fetch Problem Details ────────────────────────────────────────────────
    async def fetch_problem(self, title_slug: str) -> Dict[str, Any]:
        """
        Fetch full problem details including description, code snippets, and test cases.
        Uses LeetCode GraphQL directly for code snippets in ALL languages.
        """
        try:
            # GraphQL query for full problem data + code snippets
            graphql_query = {
                "query": """
                    query questionData($titleSlug: String!) {
                        question(titleSlug: $titleSlug) {
                            questionId
                            questionFrontendId
                            title
                            titleSlug
                            difficulty
                            content
                            topicTags { name slug }
                            hints
                            exampleTestcases
                            codeSnippets { lang langSlug code }
                            isPaidOnly
                        }
                    }
                """,
                "variables": {"titleSlug": title_slug}
            }

            response = await self.client.post(LEETCODE_GRAPHQL_URL, json=graphql_query)
            response.raise_for_status()
            data = response.json()

            question = data.get("data", {}).get("question")

            if not question:
                # Fallback to alfa API
                return await self._alfa_fetch_problem(title_slug)

            # Parse code snippets into template_code dict
            code_snippets = {}
            for snippet in (question.get("codeSnippets") or []):
                lang_slug = snippet.get("langSlug", "")
                code = snippet.get("code", "")
                if lang_slug and code:
                    code_snippets[lang_slug] = code

            # Parse test cases
            test_cases = self._parse_test_cases(
                question.get("content", ""),
                question.get("exampleTestcases", ""),
            )

            description = self._clean_description(question.get("content", ""))

            return {
                "success": True,
                "problem": {
                    "questionId": question.get("questionFrontendId", ""),
                    "title": question.get("title", ""),
                    "titleSlug": title_slug,
                    "difficulty": question.get("difficulty", "Medium"),
                    "description": description,
                    "topicTags": [t.get("name", "") for t in (question.get("topicTags") or [])],
                    "hints": question.get("hints", []),
                    "exampleTestcases": question.get("exampleTestcases", ""),
                    "testCases": test_cases,
                    "codeSnippets": code_snippets,  # ALL languages from LeetCode
                    "isPaidOnly": question.get("isPaidOnly", False),
                    "link": f"https://leetcode.com/problems/{title_slug}",
                },
            }
        except Exception as e:
            logger.warning("graphql_fetch_failed", slug=title_slug, error=str(e))
            return await self._alfa_fetch_problem(title_slug)

    async def _alfa_fetch_problem(self, title_slug: str) -> Dict[str, Any]:
        """Fallback to alfa-leetcode-api for problem details."""
        try:
            url = f"{LEETCODE_API_BASE}/select"
            response = await self.client.get(url, params={"titleSlug": title_slug})
            response.raise_for_status()
            data = response.json()

            if not data or "questionTitle" not in data:
                return {"success": False, "error": f"Problem '{title_slug}' not found"}

            test_cases = self._parse_test_cases(
                data.get("question", ""),
                data.get("exampleTestcases", ""),
            )

            description = self._clean_description(data.get("question", ""))

            return {
                "success": True,
                "problem": {
                    "questionId": data.get("questionFrontendId", ""),
                    "title": data.get("questionTitle", ""),
                    "titleSlug": title_slug,
                    "difficulty": data.get("difficulty", "Medium"),
                    "description": description,
                    "topicTags": [t.get("name", "") for t in (data.get("topicTags", []) or [])],
                    "hints": data.get("hints", []),
                    "exampleTestcases": data.get("exampleTestcases", ""),
                    "testCases": test_cases,
                    "codeSnippets": {},
                    "isPaidOnly": data.get("isPaidOnly", False),
                    "link": data.get("link", f"https://leetcode.com/problems/{title_slug}"),
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Fetch Daily Problem ──────────────────────────────────────────────────
    async def fetch_daily_problem(self) -> Dict[str, Any]:
        """Fetch today's LeetCode daily challenge."""
        try:
            graphql_query = {
                "query": """
                    query questionOfToday {
                        activeDailyCodingChallengeQuestion {
                            question {
                                titleSlug
                            }
                        }
                    }
                """
            }
            response = await self.client.post(LEETCODE_GRAPHQL_URL, json=graphql_query)
            response.raise_for_status()
            data = response.json()

            slug = (data.get("data", {})
                    .get("activeDailyCodingChallengeQuestion", {})
                    .get("question", {})
                    .get("titleSlug", ""))

            if not slug:
                # Fallback
                url = f"{LEETCODE_API_BASE}/daily"
                resp = await self.client.get(url)
                resp.raise_for_status()
                slug = resp.json().get("titleSlug", "")

            if not slug:
                return {"success": False, "error": "Could not fetch daily problem"}

            return await self.fetch_problem(slug)
        except Exception as e:
            logger.error("leetcode_daily_failed", error=str(e))
            return {"success": False, "error": str(e)}

    # ── Convert to Local Challenge Format ────────────────────────────────────
    def convert_to_challenge_format(
        self,
        problem: Dict[str, Any],
        custom_test_cases: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Convert a fetched LeetCode problem to the local CodingChallenge format.
        
        Uses official LeetCode code snippets (all languages) when available,
        falls back to generated stubs.
        """
        test_cases = custom_test_cases or problem.get("testCases", [])

        # Use official code snippets from LeetCode (ALL languages)
        code_snippets = problem.get("codeSnippets", {})

        # Build template_code with all available languages
        template_code = {}

        if code_snippets:
            # Map LeetCode langSlug to our language keys
            lang_mapping = {
                "python3": "python",
                "python": "python",
                "javascript": "javascript",
                "cpp": "cpp",
                "c": "c",
                "java": "java",
                "typescript": "typescript",
                "go": "go",
                "rust": "rust",
                "csharp": "csharp",
                "kotlin": "kotlin",
                "swift": "swift",
                "ruby": "ruby",
                "scala": "scala",
                "php": "php",
            }

            for lc_slug, our_key in lang_mapping.items():
                if lc_slug in code_snippets:
                    snippet = code_snippets[lc_slug]
                    
                    # Add standard warnings based on language comment style
                    if our_key in ["python", "ruby"]:
                        warning = "# ⚠️ NOTE: This problem was imported from LeetCode.\n# Our platform evaluates code via Standard Input/Output (like HackerRank).\n# You MUST write code that reads from stdin, calls your function, and prints to stdout.\n# You must also define any required classes (e.g., TreeNode, ListNode).\n\n"
                    elif our_key == "sql":
                        warning = "-- ⚠️ NOTE: This problem was imported from LeetCode.\n-- Please ensure your query matches the schema provided in the description.\n\n"
                    else:
                        warning = "/* ⚠️ NOTE: This problem was imported from LeetCode.\n * Our platform evaluates code via Standard Input/Output (like HackerRank).\n * You MUST write a main method that reads from stdin, calls your function, and prints to stdout.\n * You must also define any required classes (e.g., TreeNode, ListNode) yourself.\n */\n\n"
                    
                    template_code[our_key] = warning + snippet

        # Fallback: generate basic stubs if no snippets available
        if not template_code:
            func_name = self._slug_to_function_name(problem.get("titleSlug", "solution"))
            template_code = {
                "python": f'class Solution:\n    def {func_name}(self):\n        # Your solution here\n        pass\n',
                "javascript": f'/**\n * @param {{void}}\n * @return {{void}}\n */\nvar {func_name} = function() {{\n    // Your solution here\n}};\n',
                "cpp": f'class Solution {{\npublic:\n    void {func_name}() {{\n        // Your solution here\n    }}\n}};\n',
                "java": f'class Solution {{\n    public void {func_name}() {{\n        // Your solution here\n    }}\n}}\n',
            }

        return {
            "title": f"[LC] {problem.get('title', 'Unknown')}",
            "description": problem.get("description", ""),
            "difficulty": problem.get("difficulty", "Medium"),
            "template_code": template_code,
            "test_cases": test_cases,
            "time_limit": 5.0,
            "memory_limit": 256,
            "source": "leetcode",
            "source_slug": problem.get("titleSlug", ""),
            "source_link": problem.get("link", ""),
            "topic_tags": problem.get("topicTags", []),
        }

    # ── Internal Helpers ─────────────────────────────────────────────────────

    def _parse_test_cases(self, question_html: str, example_testcases_raw: str) -> List[Dict[str, str]]:
        """Parse example test cases from LeetCode problem."""
        test_cases = []

        # Strategy 1: Parse "Input: ... Output: ..." from description
        examples = re.findall(
            r'Input:\s*(.*?)\s*Output:\s*(.*?)(?:\s*Explanation:|$|\n\s*\n)',
            question_html,
            re.DOTALL
        )

        for inp, out in examples:
            inp_clean = inp.strip().replace("\n", " ")
            out_clean = out.strip().replace("\n", " ")
            test_cases.append({
                "input": inp_clean,
                "expected_output": out_clean,
                "is_hidden": False,
            })

        # If we couldn't parse from HTML, try the raw exampleTestcases
        if not test_cases and example_testcases_raw:
            lines = [l.strip() for l in example_testcases_raw.strip().split("\n") if l.strip()]
            for line in lines:
                test_cases.append({
                    "input": line,
                    "expected_output": "",
                    "is_hidden": False,
                    "needs_verification": True,
                })

        return test_cases

    def _clean_description(self, html: str) -> str:
        """Convert LeetCode HTML description to clean markdown-ish text."""
        if not html:
            return ""

        text = html
        text = re.sub(r'</?p>', '\n', text)
        text = re.sub(r'</?strong>', '**', text)
        text = re.sub(r'</?em>', '*', text)
        text = re.sub(r'</?code>', '`', text)
        text = re.sub(r'<pre[^>]*>', '\n```\n', text)
        text = re.sub(r'</pre>', '\n```\n', text)
        text = re.sub(r'</?ul>', '\n', text)
        text = re.sub(r'<li>', '- ', text)
        text = re.sub(r'</li>', '\n', text)
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<sup>', '^', text)
        text = re.sub(r'</sup>', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()

        return text

    def _slug_to_function_name(self, slug: str) -> str:
        """Convert 'two-sum' to 'twoSum'."""
        parts = slug.split("-")
        if not parts:
            return "solution"
        return parts[0] + "".join(p.capitalize() for p in parts[1:])


# ── Singleton Instance ───────────────────────────────────────────────────────
leetcode_service = LeetCodeService()
