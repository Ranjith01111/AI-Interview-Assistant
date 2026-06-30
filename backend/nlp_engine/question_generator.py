"""
Question Generator — Selects appropriate questions from the bank based on resume data.

Maps detected skills to relevant categories, filters by experience level,
and ensures variety in the final question set.
"""

import random
from typing import List, Dict, Optional, Tuple
from .resume_parser import ParsedResume, ResumeParser
from .question_bank import QuestionBank, Question, get_question_bank


# Mapping from detected skill categories to question bank categories
SKILL_TO_CATEGORY_MAP: Dict[str, List[str]] = {
    "python": ["python"],
    "javascript": ["javascript"],
    "react": ["react"],
    "sql": ["sql"],
    "nosql": ["sql"],  # NoSQL still draws from SQL category (covers both)
    "aws": ["aws"],
    "cloud_general": ["aws"],
    "docker": ["docker"],
    "machine_learning": ["machine_learning"],
    "data_science": ["machine_learning"],
    "system_design": ["system_design"],
    "devops": ["docker", "aws"],
    "git": ["git"],
    "testing": ["testing"],
    "security": ["security"],
    "api_design": ["api_design"],
    "data_structures": ["data_structures"],
    "java": ["python"],  # Map to closest category (general programming)
    "csharp": ["python"],
    "go": ["python"],
    "rust": ["python"],
    "mobile": ["react", "javascript"],
}

# Default question distribution for a standard interview
DEFAULT_DISTRIBUTION = {
    "technical": 0.70,  # 70% technical
    "hr": 0.30,  # 30% behavioral/HR
}


class QuestionGenerator:
    """Generates interview questions based on resume analysis."""

    def __init__(self, question_bank: Optional[QuestionBank] = None):
        self.bank = question_bank or get_question_bank()
        self.parser = ResumeParser()

    def generate_from_resume(
        self,
        parsed_resume: ParsedResume,
        num_questions: int = 10,
        include_behavioral: bool = True,
        difficulty_override: Optional[str] = None,
    ) -> List[Question]:
        """
        Generate a tailored question set based on parsed resume data.

        Args:
            parsed_resume: Structured resume data from ResumeParser
            num_questions: Total number of questions to generate
            include_behavioral: Whether to include HR/behavioral questions
            difficulty_override: Force a specific difficulty level

        Returns:
            List of selected questions tailored to the candidate
        """
        # Determine appropriate difficulty
        if difficulty_override:
            difficulty = difficulty_override
        else:
            difficulty = self.parser.get_difficulty_for_experience(
                parsed_resume.experience_years
            )

        # Get allowed difficulty levels (include easier questions too)
        allowed_difficulties = self._get_difficulty_range(difficulty)

        # Determine relevant categories from resume skills
        relevant_categories = self._map_skills_to_categories(
            parsed_resume.skill_categories
        )

        # Calculate distribution
        if include_behavioral:
            num_technical = int(num_questions * DEFAULT_DISTRIBUTION["technical"])
            num_behavioral = num_questions - num_technical
        else:
            num_technical = num_questions
            num_behavioral = 0

        # Select technical questions
        technical_questions = self._select_technical_questions(
            relevant_categories, allowed_difficulties, num_technical
        )

        # Select behavioral questions
        behavioral_questions = self._select_behavioral_questions(
            allowed_difficulties, num_behavioral
        )

        # Combine and shuffle
        all_questions = technical_questions + behavioral_questions
        random.shuffle(all_questions)

        return all_questions

    def generate_for_skills(
        self,
        skills: List[str],
        experience_years: float = 3.0,
        num_questions: int = 10,
        include_behavioral: bool = True,
    ) -> List[Question]:
        """
        Generate questions directly from a list of skills (without resume parsing).

        Args:
            skills: List of skill keywords
            experience_years: Years of experience for difficulty calibration
            num_questions: Total number of questions
            include_behavioral: Include HR/behavioral questions

        Returns:
            List of selected questions
        """
        # Create a minimal ParsedResume
        resume = ParsedResume(
            skills=skills,
            experience_years=experience_years,
            skill_categories=self._categorize_skills_list(skills),
        )
        return self.generate_from_resume(
            resume, num_questions, include_behavioral
        )

    def generate_for_category(
        self,
        category: str,
        difficulty: str = "medium",
        num_questions: int = 5,
    ) -> List[Question]:
        """
        Generate questions for a specific category and difficulty.

        Args:
            category: Question category (python, javascript, etc.)
            difficulty: Difficulty level (easy, medium, hard)
            num_questions: Number of questions to select

        Returns:
            List of questions from the specified category
        """
        pool = self.bank.filter_questions(
            categories=[category],
            difficulties=[difficulty],
        )

        if not pool:
            # Fallback to any difficulty in that category
            pool = self.bank.get_by_category(category)

        if not pool:
            return []

        return random.sample(pool, min(num_questions, len(pool)))

    def generate_mixed_interview(
        self,
        num_questions: int = 15,
        difficulty: str = "medium",
        focus_categories: Optional[List[str]] = None,
    ) -> List[Question]:
        """
        Generate a mixed interview covering multiple areas.
        Useful when no resume is available.

        Args:
            num_questions: Total questions
            difficulty: Target difficulty
            focus_categories: Optional category focus (otherwise all)

        Returns:
            Diverse question set
        """
        allowed_difficulties = self._get_difficulty_range(difficulty)

        if focus_categories:
            categories = focus_categories
        else:
            # Default broad categories for a general interview
            categories = [
                "python", "javascript", "sql", "behavioral"
            ]

        # Ensure behavioral is included
        if "behavioral" not in categories:
            categories.append("behavioral")

        return self.bank.random_selection(
            n=num_questions,
            categories=categories,
            difficulties=allowed_difficulties,
            ensure_variety=True,
        )

    def _map_skills_to_categories(
        self, skill_categories: Dict[str, List[str]]
    ) -> List[str]:
        """Map detected skill categories to question bank categories."""
        question_categories = set()

        for skill_cat in skill_categories.keys():
            mapped = SKILL_TO_CATEGORY_MAP.get(skill_cat, [])
            question_categories.update(mapped)

        # If no skills detected, return broad defaults
        if not question_categories:
            question_categories = {
                "python", "javascript", "sql"
            }

        return list(question_categories)

    def _get_difficulty_range(self, target: str) -> List[str]:
        """Get allowed difficulty levels based on target."""
        if target == "easy":
            return ["easy"]
        elif target == "medium":
            return ["easy", "medium"]
        else:  # hard
            return ["medium", "hard"]

    def _select_technical_questions(
        self,
        categories: List[str],
        difficulties: List[str],
        count: int,
    ) -> List[Question]:
        """Select technical questions ensuring variety across categories."""
        if not categories:
            return []

        # Pool all matching questions
        pool = self.bank.filter_questions(
            categories=categories,
            difficulties=difficulties,
            question_type="technical",
        )

        if not pool:
            # Fallback: any technical question at right difficulty, EXCLUDING advanced categories
            # unless they were explicitly in the requested categories
            pool = self.bank.filter_questions(
                difficulties=difficulties,
                question_type="technical",
            )
            # Filter out system_design and data_structures unless explicitly requested
            excluded = {"system_design", "data_structures"} - set(categories)
            pool = [q for q in pool if q.category not in excluded]

        if not pool:
            return []

        # Select with variety
        selected = []
        category_usage: Dict[str, int] = {cat: 0 for cat in categories}
        questions_per_category = max(1, count // len(categories))

        random.shuffle(pool)

        # First pass: ensure each category gets representation
        for cat in categories:
            cat_questions = [q for q in pool if q.category == cat and q not in selected]
            take = min(questions_per_category, len(cat_questions))
            selected.extend(random.sample(cat_questions, take) if cat_questions else [])

        # Fill remaining slots
        remaining = [q for q in pool if q not in selected]
        while len(selected) < count and remaining:
            choice = random.choice(remaining)
            selected.append(choice)
            remaining.remove(choice)

        return selected[:count]

    def _select_behavioral_questions(
        self, difficulties: List[str], count: int
    ) -> List[Question]:
        """Select behavioral/HR questions."""
        if count <= 0:
            return []

        pool = self.bank.filter_questions(
            categories=["behavioral"],
            difficulties=difficulties,
            question_type="hr",
        )

        if not pool:
            # Fallback: any behavioral question
            pool = self.bank.get_by_category("behavioral")

        if not pool:
            return []

        return random.sample(pool, min(count, len(pool)))

    def _categorize_skills_list(self, skills: List[str]) -> Dict[str, List[str]]:
        """Convert a flat skills list into categorized format."""
        from .resume_parser import SKILL_KEYWORDS
        import re

        categorized: Dict[str, List[str]] = {}
        skills_lower = [s.lower() for s in skills]

        for category, keywords in SKILL_KEYWORDS.items():
            matched = []
            for kw in keywords:
                if kw.lower() in skills_lower:
                    matched.append(kw)
            if matched:
                categorized[category] = matched

        # If nothing matched, try fuzzy matching
        if not categorized:
            for skill in skills_lower:
                for category, keywords in SKILL_KEYWORDS.items():
                    for kw in keywords:
                        if skill in kw or kw in skill:
                            if category not in categorized:
                                categorized[category] = []
                            categorized[category].append(kw)
                            break

        return categorized

    def get_question_categories_for_resume(
        self, parsed_resume: ParsedResume
    ) -> Dict[str, int]:
        """
        Get a breakdown of available questions per category for a resume.
        Useful for UI display of what areas will be covered.
        """
        relevant_categories = self._map_skills_to_categories(
            parsed_resume.skill_categories
        )
        difficulty = self.parser.get_difficulty_for_experience(
            parsed_resume.experience_years
        )
        allowed_difficulties = self._get_difficulty_range(difficulty)

        breakdown = {}
        for cat in relevant_categories:
            questions = self.bank.filter_questions(
                categories=[cat],
                difficulties=allowed_difficulties,
            )
            breakdown[cat] = len(questions)

        behavioral = self.bank.filter_questions(
            categories=["behavioral"],
            difficulties=allowed_difficulties,
        )
        breakdown["behavioral"] = len(behavioral)
        return breakdown



# ── Convenience function (matches service imports) ────────────────────
_generator_instance = None

def generate_questions_for_candidate(
    skills: list,
    experience_years: str = "Not specified",
    experience_level: str = "mid",
    num_questions: int = 10,
    focus_categories: list = [],
    difficulty_override: str = None,
) -> list:
    """
    Generate interview questions for a candidate.
    
    This is the main entry point used by question_service.py.
    
    Returns:
        List of dicts with: question, topic, difficulty, category, type, expected_keywords
    """
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = QuestionGenerator()
    
    # Parse experience years from string like "3+ years" to float
    exp_float = 3.0
    if isinstance(experience_years, (int, float)):
        exp_float = float(experience_years)
    elif isinstance(experience_years, str):
        import re
        match = re.search(r"(\d+)", experience_years)
        if match:
            exp_float = float(match.group(1))
    
    # If focus_categories are provided, use them directly
    if focus_categories and len(focus_categories) > 0:
        questions = _generator_instance.generate_mixed_interview(
            num_questions=num_questions,
            difficulty=difficulty_override or _level_to_difficulty(experience_level),
            focus_categories=focus_categories,
        )
    elif difficulty_override:
        # Use skills-based but with forced difficulty
        questions = _generator_instance.generate_for_skills(
            skills=skills if skills else ["general"],
            experience_years=exp_float,
            num_questions=num_questions,
            include_behavioral=True,
        )
    else:
        # Default: skills-based generation
        questions = _generator_instance.generate_for_skills(
            skills=skills if skills else ["general"],
            experience_years=exp_float,
            num_questions=num_questions,
            include_behavioral=True,
        )
    
    # Convert Question dataclass objects to dicts
    result = []
    for idx, q in enumerate(questions, start=1):
        result.append({
            "id": idx,
            "question": q.text,
            "topic": q.topic,
            "difficulty": q.difficulty,
            "category": q.category,
            "type": q.question_type,
            "expected_keywords": q.expected_keywords,
            "model_answer_hint": q.model_answer_hint,
            "project_reference": None,
        })
    
    return result


def _level_to_difficulty(level: str) -> str:
    """Map experience level to difficulty string."""
    mapping = {
        "junior": "easy",
        "mid": "medium",
        "senior": "hard",
        "lead": "hard",
    }
    return mapping.get(level, "medium")
