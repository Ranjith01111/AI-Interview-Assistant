"""
Comprehensive Test Suite: NLP Engine

Covers:
  • Resume parser with various skill patterns (Python, JS, React, AWS, ML, etc.)
  • Resume parser edge cases: Unicode, minimal, empty, no-skills, fresher
  • Question generator distribution and difficulty calibration
  • Answer evaluator scoring: keyword matching, TF-IDF, edge cases
  • Feedback generator output format and tiers

Uses pytest + pytest-asyncio. All tests are synchronous (NLP engine is sync).
"""

import pytest
import re
from unittest.mock import patch

from backend.nlp_engine.resume_parser import (
    ResumeParser,
    ParsedResume,
    parse_resume_structured,
    _extract_candidate_name,
    SKILL_KEYWORDS,
)
from backend.nlp_engine.question_generator import (
    QuestionGenerator,
    generate_questions_for_candidate,
)
from backend.nlp_engine.answer_evaluator import (
    AnswerEvaluator,
    EvaluationResult,
    evaluate_answer,
    KEYWORD_WEIGHT,
    LENGTH_WEIGHT,
    RELEVANCE_WEIGHT,
)
from backend.nlp_engine.feedback_generator import (
    FeedbackGenerator,
    generate_feedback,
    generate_final_summary,
    EXCELLENT_THRESHOLD,
    GOOD_THRESHOLD,
    ADEQUATE_THRESHOLD,
)
from backend.nlp_engine.question_bank import Question, QuestionBank, get_question_bank


# ══════════════════════════════════════════════════════════════════════════════
# RESUME PARSER — SKILL PATTERN TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestResumeParserSkillPatterns:
    """Tests for detecting various technology skill patterns in resumes."""

    @pytest.fixture
    def parser(self):
        return ResumeParser()

    # --- Python ecosystem ---

    def test_detects_python_core_skills(self, parser):
        """Should detect Python, Django, Flask, FastAPI."""
        text = """
        Senior Python Developer
        Skills: Python, Django, Flask, FastAPI, Celery, SQLAlchemy
        5 years experience building web applications.
        """
        result = parser.parse(text)
        skills_lower = [s.lower() for s in result.skills]
        assert "python" in skills_lower
        assert "django" in skills_lower
        assert "flask" in skills_lower
        assert "fastapi" in skills_lower

    def test_detects_python_data_science_skills(self, parser):
        """Should detect pandas, numpy, scipy."""
        text = """
        Data Scientist
        Skills: Python, Pandas, NumPy, SciPy, Matplotlib, Jupyter
        3 years of experience in data analysis and ML.
        """
        result = parser.parse(text)
        skills_lower = [s.lower() for s in result.skills]
        assert "pandas" in skills_lower
        assert "numpy" in skills_lower

    # --- JavaScript/TypeScript ecosystem ---

    def test_detects_javascript_stack(self, parser):
        """Should detect Node.js, TypeScript, Express."""
        text = """
        Full Stack Developer
        Technologies: JavaScript, TypeScript, Node.js, Express, Webpack, Jest
        Built REST APIs with Node.js and Express.
        """
        result = parser.parse(text)
        skills_lower = [s.lower() for s in result.skills]
        assert "javascript" in skills_lower
        assert "typescript" in skills_lower
        assert any("node" in s for s in skills_lower)

    # --- React ecosystem ---

    def test_detects_react_ecosystem(self, parser):
        """Should detect React, Redux, React Router."""
        text = """
        Frontend Engineer
        Experience with React, Redux, React Hooks, Material-UI, Storybook
        Built SPAs using React and managed state with Redux.
        """
        result = parser.parse(text)
        skills_lower = [s.lower() for s in result.skills]
        assert "react" in skills_lower
        assert "redux" in skills_lower

    # --- AWS / Cloud ---

    def test_detects_aws_services(self, parser):
        """Should detect AWS services: EC2, S3, Lambda, etc."""
        text = """
        Cloud Engineer — AWS Certified
        Deployed applications on AWS EC2, S3, Lambda, RDS, and ECS.
        Used Terraform for infrastructure as code and CloudWatch for monitoring.
        """
        result = parser.parse(text)
        skills_lower = [s.lower() for s in result.skills]
        assert "aws" in skills_lower
        assert "ec2" in skills_lower
        assert "s3" in skills_lower
        assert "lambda" in skills_lower
        assert "terraform" in skills_lower

    # --- Docker / Kubernetes ---

    def test_detects_container_skills(self, parser):
        """Should detect Docker, Kubernetes, Helm."""
        text = """
        DevOps Engineer
        Skills: Docker, Docker Compose, Kubernetes, Helm, Istio
        Managed containerized microservices in K8s clusters.
        """
        result = parser.parse(text)
        skills_lower = [s.lower() for s in result.skills]
        assert "docker" in skills_lower
        assert "kubernetes" in skills_lower or "k8s" in skills_lower

    # --- Machine Learning ---

    def test_detects_ml_skills(self, parser):
        """Should detect ML frameworks and concepts."""
        text = """
        Machine Learning Engineer
        Skills: TensorFlow, PyTorch, Scikit-learn, NLP, Computer Vision
        Built deep learning models with CNNs and transformers.
        Experience with MLOps and model deployment.
        """
        result = parser.parse(text)
        skills_lower = [s.lower() for s in result.skills]
        assert "tensorflow" in skills_lower
        assert "pytorch" in skills_lower

    # --- Database ---

    def test_detects_database_skills(self, parser):
        """Should detect SQL and NoSQL databases."""
        text = """
        Backend Developer
        Databases: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch
        Designed schemas and optimized queries for high-traffic apps.
        """
        result = parser.parse(text)
        skills_lower = [s.lower() for s in result.skills]
        assert "postgresql" in skills_lower or "postgres" in skills_lower
        assert "mongodb" in skills_lower
        assert "redis" in skills_lower

    # --- Skill categorization ---

    def test_categorizes_skills_correctly(self, parser):
        """Skills should be grouped into correct categories."""
        text = """
        Full Stack Engineer
        Python, Django, React, PostgreSQL, Docker, AWS, Git
        """
        result = parser.parse(text)
        categories = result.skill_categories
        assert "python" in categories
        assert "react" in categories or any("react" in str(v) for v in categories.values())
        assert "docker" in categories or "aws" in categories

    def test_skill_patterns_case_insensitive(self, parser):
        """Skill detection should be case-insensitive."""
        text = "Technologies: PYTHON, fastAPI, REACT, docker, AWS"
        result = parser.parse(text)
        assert len(result.skills) >= 4


# ══════════════════════════════════════════════════════════════════════════════
# RESUME PARSER — EXPERIENCE EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════


class TestResumeParserExperience:
    """Tests for experience years extraction from varied formats."""

    @pytest.fixture
    def parser(self):
        return ResumeParser()

    def test_explicit_years_format(self, parser):
        """Should detect '5 years of experience'."""
        text = "Senior Developer with 5 years of experience in Python."
        result = parser.parse(text)
        assert result.experience_years == 5.0

    def test_plus_years_format(self, parser):
        """Should detect '7+ years experience'."""
        text = "Experienced engineer with 7+ years experience in distributed systems."
        result = parser.parse(text)
        assert result.experience_years == 7.0

    def test_over_x_years_format(self, parser):
        """Should detect 'over 10 years'."""
        text = "Principal engineer with over 10 years in software development."
        result = parser.parse(text)
        assert result.experience_years == 10.0

    def test_fresher_detection(self, parser):
        """Should detect fresher/entry-level candidates."""
        text = """
        Recent Graduate
        Entry-level software developer seeking my first role.
        B.Tech Computer Science — 2024
        """
        result = parser.parse(text)
        assert result.experience_years == 0.0

    def test_student_detection(self, parser):
        """Current students should be detected as freshers."""
        text = """
        Computer Science Student
        Seeking a software engineering internship.
        Skills: Python, Java, Git
        """
        result = parser.parse(text)
        assert result.experience_years == 0.0

    def test_no_experience_mentioned_returns_zero(self, parser):
        """If no experience info at all, should return 0."""
        text = """
        Alice Johnson
        Software Developer
        Python, React, Docker
        """
        result = parser.parse(text)
        assert result.experience_years == 0.0

    def test_date_range_calculation(self, parser):
        """Should calculate years from work date ranges."""
        text = """
        Work Experience
        Software Engineer — Acme Corp (2019 - 2023)
        Junior Developer — StartupXYZ (2017 - 2019)
        """
        result = parser.parse(text)
        assert result.experience_years >= 4.0

    def test_experience_level_classification(self, parser):
        """get_experience_level should classify correctly."""
        assert parser.get_experience_level(1.0) == "junior"
        assert parser.get_experience_level(2.0) == "junior"
        assert parser.get_experience_level(3.0) == "mid"
        assert parser.get_experience_level(5.0) == "mid"
        assert parser.get_experience_level(7.0) == "senior"
        assert parser.get_experience_level(12.0) == "expert"

    def test_difficulty_for_experience(self, parser):
        """get_difficulty_for_experience should map correctly."""
        assert parser.get_difficulty_for_experience(1.0) == "easy"
        assert parser.get_difficulty_for_experience(3.0) == "medium"
        assert parser.get_difficulty_for_experience(8.0) == "hard"


# ══════════════════════════════════════════════════════════════════════════════
# RESUME PARSER — NAME EXTRACTION & CONVENIENCE FUNCTION
# ══════════════════════════════════════════════════════════════════════════════


class TestResumeParserNameAndConvenience:
    """Tests for candidate name extraction and the parse_resume_structured function."""

    def test_extracts_name_from_first_line(self):
        """Name on the first line should be detected."""
        text = "John Smith\nSenior Software Engineer\nPython, React"
        name = _extract_candidate_name(text)
        assert "John" in name and "Smith" in name

    def test_extracts_multipart_name(self):
        """Three-part names should work."""
        text = "Mary Jane Watson\nFull Stack Developer"
        name = _extract_candidate_name(text)
        assert "Mary" in name

    def test_defaults_to_candidate_when_no_name(self):
        """Should return 'Candidate' when no name-like line found."""
        text = "Skills: Python, React, Docker\nExperience: 5 years"
        name = _extract_candidate_name(text)
        assert name == "Candidate"

    def test_parse_resume_structured_returns_all_keys(self):
        """parse_resume_structured should return dict with all expected keys."""
        text = """
        Alice Developer
        Software Engineer
        5 years of experience with Python, React, AWS, Docker.
        """
        result = parse_resume_structured(text)
        expected_keys = [
            "candidate_name", "skills", "skills_categorized",
            "experience_years", "experience_level", "difficulty",
            "job_titles", "projects", "education", "certifications", "summary",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_parse_resume_structured_empty_text(self):
        """Empty text should not crash."""
        result = parse_resume_structured("")
        assert isinstance(result, dict)
        assert isinstance(result["skills"], list)
        assert result["experience_years"] == 0.0

    def test_parse_resume_structured_unicode(self):
        """Unicode characters should not crash the parser."""
        text = "José García\nDéveloppeur Senior\n5 años de experiencia\nPython, Django, React"
        result = parse_resume_structured(text)
        assert isinstance(result["skills"], list)
        assert len(result["skills"]) > 0

    def test_parse_resume_structured_gibberish(self):
        """Random gibberish text should not crash."""
        text = "asdf jkl; qwer uiop zxcv bnm, !@#$ %^&* () 12345"
        result = parse_resume_structured(text)
        assert isinstance(result, dict)
        assert result["experience_years"] >= 0


# ══════════════════════════════════════════════════════════════════════════════
# QUESTION GENERATOR — DISTRIBUTION TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestQuestionGeneratorDistribution:
    """Tests for question selection distribution and variety."""

    @pytest.fixture
    def generator(self):
        return QuestionGenerator()

    @pytest.fixture
    def python_resume(self):
        return ParsedResume(
            skills=["python", "django", "fastapi", "postgresql", "docker", "aws"],
            experience_years=4.0,
            job_titles=["Software Engineer"],
            skill_categories={
                "python": ["python", "django", "fastapi"],
                "sql": ["postgresql"],
                "docker": ["docker"],
                "aws": ["aws"],
            },
        )

    @pytest.fixture
    def frontend_resume(self):
        return ParsedResume(
            skills=["javascript", "react", "typescript", "redux", "css", "webpack"],
            experience_years=3.0,
            skill_categories={
                "javascript": ["javascript", "typescript"],
                "react": ["react", "redux"],
            },
        )

    def test_generates_exact_count(self, generator, python_resume):
        """Should generate exactly the requested number of questions."""
        for count in [5, 10, 15]:
            questions = generator.generate_from_resume(python_resume, num_questions=count)
            assert len(questions) == count

    def test_technical_behavioral_ratio(self, generator, python_resume):
        """When behavioral included, ~70% technical / ~30% behavioral."""
        questions = generator.generate_from_resume(
            python_resume, num_questions=20, include_behavioral=True
        )
        behavioral_count = sum(
            1 for q in questions if q.question_type in ("hr", "behavioral")
        )
        technical_count = len(questions) - behavioral_count
        # 70% of 20 = 14 technical, 30% = 6 behavioral (approximately)
        assert technical_count >= 10  # At least some technical
        assert behavioral_count >= 3  # At least some behavioral

    def test_no_behavioral_when_disabled(self, generator, python_resume):
        """When behavioral disabled, all questions should be technical."""
        questions = generator.generate_from_resume(
            python_resume, num_questions=10, include_behavioral=False
        )
        for q in questions:
            assert q.question_type == "technical"
            assert q.category not in ("behavioral", "hr")

    def test_questions_relevant_to_python_resume(self, generator, python_resume):
        """Python resume should get Python/SQL/Docker/AWS questions."""
        questions = generator.generate_from_resume(python_resume, num_questions=15)
        categories = set(q.category for q in questions)
        # Should include categories related to detected skills
        relevant = {"python", "sql", "docker", "aws", "system_design", "data_structures"}
        overlap = categories & relevant
        assert len(overlap) >= 2, f"Expected relevant categories, got: {categories}"

    def test_questions_relevant_to_frontend_resume(self, generator, frontend_resume):
        """Frontend resume should get React/JS questions."""
        questions = generator.generate_from_resume(frontend_resume, num_questions=15)
        categories = set(q.category for q in questions)
        relevant = {"javascript", "react", "system_design", "data_structures"}
        overlap = categories & relevant
        assert len(overlap) >= 1, f"Expected frontend categories, got: {categories}"

    def test_variety_across_categories(self, generator, python_resume):
        """Questions should come from multiple categories, not all one."""
        questions = generator.generate_from_resume(python_resume, num_questions=15)
        categories = set(q.category for q in questions)
        # Should have at least 3 different categories in 15 questions
        assert len(categories) >= 3

    def test_generate_for_skills_convenience(self):
        """generate_questions_for_candidate convenience function should work."""
        result = generate_questions_for_candidate(
            skills=["python", "react", "docker"],
            experience_years="3",
            num_questions=8,
        )
        assert len(result) == 8
        for q in result:
            assert "question" in q
            assert "difficulty" in q
            assert "category" in q
            assert "expected_keywords" in q

    def test_generate_for_empty_skills(self):
        """Empty skills should still produce questions (general fallback)."""
        result = generate_questions_for_candidate(
            skills=[],
            experience_years="0",
            num_questions=5,
        )
        assert len(result) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# QUESTION GENERATOR — DIFFICULTY CALIBRATION
# ══════════════════════════════════════════════════════════════════════════════


class TestQuestionGeneratorDifficulty:
    """Tests for difficulty calibration based on experience level."""

    @pytest.fixture
    def generator(self):
        return QuestionGenerator()

    def test_junior_gets_easy_questions(self, generator):
        """Junior (1 year) should get mostly easy questions."""
        junior = ParsedResume(
            skills=["python", "git"],
            experience_years=1.0,
            skill_categories={"python": ["python"], "git": ["git"]},
        )
        questions = generator.generate_from_resume(junior, num_questions=10)
        difficulties = [q.difficulty for q in questions]
        # Junior should get easy difficulty level — range includes only "easy"
        hard_count = sum(1 for d in difficulties if d == "hard")
        assert hard_count == 0, "Junior should not get hard questions"

    def test_mid_gets_easy_and_medium(self, generator):
        """Mid-level (3-4 years) should get easy+medium."""
        mid = ParsedResume(
            skills=["python", "django", "docker"],
            experience_years=4.0,
            skill_categories={"python": ["python", "django"], "docker": ["docker"]},
        )
        questions = generator.generate_from_resume(mid, num_questions=10)
        difficulties = [q.difficulty for q in questions]
        # Should be easy/medium, not hard
        hard_count = sum(1 for d in difficulties if d == "hard")
        assert hard_count == 0, "Mid-level should not get hard questions"

    def test_senior_gets_medium_and_hard(self, generator):
        """Senior (8+ years) should get medium+hard."""
        senior = ParsedResume(
            skills=["python", "aws", "kubernetes", "system design"],
            experience_years=8.0,
            skill_categories={
                "python": ["python"],
                "aws": ["aws"],
                "docker": ["kubernetes"],
            },
        )
        questions = generator.generate_from_resume(senior, num_questions=10)
        difficulties = [q.difficulty for q in questions]
        # Should NOT get easy questions for senior
        easy_count = sum(1 for d in difficulties if d == "easy")
        assert easy_count == 0, "Senior should not get easy questions"

    def test_difficulty_override(self, generator):
        """difficulty_override should force specific difficulty."""
        resume = ParsedResume(
            skills=["python"],
            experience_years=1.0,  # normally easy
            skill_categories={"python": ["python"]},
        )
        questions = generator.generate_from_resume(
            resume, num_questions=5, difficulty_override="hard"
        )
        difficulties = [q.difficulty for q in questions]
        # With hard override, should get medium/hard only
        easy_count = sum(1 for d in difficulties if d == "easy")
        assert easy_count == 0


# ══════════════════════════════════════════════════════════════════════════════
# ANSWER EVALUATOR — KEYWORD MATCHING
# ══════════════════════════════════════════════════════════════════════════════


class TestAnswerEvaluatorKeywords:
    """Tests for keyword-based scoring in the answer evaluator."""

    @pytest.fixture
    def evaluator(self):
        return AnswerEvaluator()

    def _make_question(self, text="Test question?", keywords=None, difficulty="medium"):
        return Question(
            id="test_q",
            text=text,
            topic="test",
            difficulty=difficulty,
            category="python",
            question_type="technical",
            expected_keywords=keywords or [],
            model_answer_hint="Test model answer.",
        )

    def test_all_keywords_found(self, evaluator):
        """Answer containing all keywords should get high keyword score."""
        q = self._make_question(
            text="What is a Python decorator?",
            keywords=["function", "wrapper", "modify", "behavior", "@"],
        )
        result = evaluator.evaluate(
            "A decorator is a function that wraps another function using @ syntax "
            "to modify its behavior without changing its source code.",
            q,
        )
        assert result.keyword_score >= 7.0
        assert len(result.keywords_found) >= 4

    def test_no_keywords_found(self, evaluator):
        """Answer with zero keyword matches should get low keyword score."""
        q = self._make_question(
            keywords=["binary tree", "traversal", "recursion", "nodes", "depth"],
        )
        result = evaluator.evaluate(
            "I enjoy cooking pasta and walking my dog in the park.",
            q,
        )
        assert result.keyword_score <= 2.0
        assert len(result.keywords_missed) == 5

    def test_partial_keyword_match(self, evaluator):
        """Some keywords found should give moderate score."""
        q = self._make_question(
            keywords=["REST", "HTTP", "stateless", "resource", "endpoint", "CRUD"],
        )
        result = evaluator.evaluate(
            "REST APIs use HTTP methods to perform CRUD operations on resources.",
            q,
        )
        assert 3.0 <= result.keyword_score <= 9.0
        assert len(result.keywords_found) >= 3

    def test_keyword_variations_detected(self, evaluator):
        """Hyphenated/spaced variations should be detected."""
        q = self._make_question(keywords=["object-oriented"])
        result = evaluator.evaluate(
            "OOP or object oriented programming is a paradigm using classes.",
            q,
        )
        # "object-oriented" should match "object oriented" variation
        assert len(result.keywords_found) >= 1 or result.keyword_score > 0

    def test_empty_keywords_list(self, evaluator):
        """No expected keywords should give neutral keyword score."""
        q = self._make_question(keywords=[])
        result = evaluator.evaluate("Any answer text here.", q)
        assert result.keyword_score == 5.0  # Neutral when no keywords defined


# ══════════════════════════════════════════════════════════════════════════════
# ANSWER EVALUATOR — EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════


class TestAnswerEvaluatorEdgeCases:
    """Tests for edge cases: empty, very short, very long, perfect answers."""

    @pytest.fixture
    def evaluator(self):
        return AnswerEvaluator()

    def _make_question(self, keywords=None, difficulty="medium"):
        return Question(
            id="test_q",
            text="Explain Python decorators.",
            topic="python",
            difficulty=difficulty,
            category="python",
            question_type="technical",
            expected_keywords=keywords or ["function", "wrapper", "modify", "behavior", "@"],
            model_answer_hint="Decorators wrap functions to modify behavior.",
        )

    def test_empty_answer_scores_zero(self, evaluator):
        """Empty string should score 0."""
        q = self._make_question()
        result = evaluator.evaluate("", q)
        assert result.score == 0.0
        assert len(result.keywords_missed) == 5
        assert len(result.improvements) > 0

    def test_whitespace_only_scores_zero(self, evaluator):
        """Whitespace-only should score 0."""
        q = self._make_question()
        result = evaluator.evaluate("   \n\t  ", q)
        assert result.score == 0.0

    def test_single_word_answer(self, evaluator):
        """Single word should score very low."""
        q = self._make_question()
        result = evaluator.evaluate("function", q)
        assert result.score <= 4.0

    def test_very_short_answer(self, evaluator):
        """Very short answer (< 10 words) should have low length score."""
        q = self._make_question()
        result = evaluator.evaluate("Decorators modify function behavior.", q)
        assert result.length_score <= 5.0

    def test_perfect_comprehensive_answer(self, evaluator):
        """A comprehensive answer hitting all keywords should score high."""
        q = self._make_question()
        answer = (
            "A Python decorator is a higher-order function that takes another function "
            "as input and returns a modified version (wrapper) of it. Decorators use the "
            "@ syntax placed above a function definition to modify its behavior without "
            "changing its source code. Common uses include logging, authentication, "
            "caching, and rate limiting. For example, @staticmethod and @property are "
            "built-in decorators. You can also create custom decorators using functools.wraps "
            "to preserve the original function's metadata. Decorators can be stacked, "
            "and they can also accept arguments when implemented as decorator factories. "
            "This pattern promotes DRY principles and separation of concerns."
        )
        result = evaluator.evaluate(answer, q)
        assert result.score >= 6.0

    def test_very_long_verbose_answer(self, evaluator):
        """Very verbose answer should not score higher than ideal."""
        q = self._make_question()
        # Generate a 600-word repetitive answer
        long_answer = "A decorator is a function wrapper that modifies behavior. " * 100
        result = evaluator.evaluate(long_answer, q)
        # Should still score OK (keywords present) but not get max length score
        assert result.score <= 10.0
        assert result.score >= 2.0  # Still has some keywords

    def test_answer_with_filler_words(self, evaluator):
        """Answers full of filler words should get slight penalty."""
        q = self._make_question()
        answer = (
            "Um, so like basically, you know, a decorator is actually literally "
            "a function, I think maybe, that like wraps another function, you know, "
            "to modify its behavior, basically. And stuff like that, etc."
        )
        result = evaluator.evaluate(answer, q)
        # Should still find keywords but quality modifier penalizes fillers
        assert result.keywords_found  # Some keywords detected

    def test_answer_with_examples_gets_bonus(self, evaluator):
        """Structured answer with examples should get quality bonus."""
        q = self._make_question()
        answer = (
            "A decorator is a function that wraps another function to modify its "
            "behavior. For example, you can create a logging decorator:\n"
            "1. First, define the outer function that accepts a function\n"
            "2. Second, define the inner wrapper function\n"
            "3. Third, return the wrapper\n"
            "The @ syntax is syntactic sugar for applying the decorator. "
            "In practice, decorators are used in production for authentication, "
            "rate limiting, and caching."
        )
        result = evaluator.evaluate(answer, q)
        assert result.score >= 5.0

    def test_score_always_0_to_10(self, evaluator):
        """Score should always be clamped between 0 and 10."""
        q = self._make_question()
        test_answers = [
            "",
            "x",
            "A" * 10000,
            "function wrapper modify behavior @" * 50,
            "completely irrelevant off topic answer about cooking",
        ]
        for answer in test_answers:
            result = evaluator.evaluate(answer, q)
            assert 0.0 <= result.score <= 10.0, f"Score {result.score} out of range"

    def test_evaluation_result_has_all_fields(self, evaluator):
        """EvaluationResult should have all required fields."""
        q = self._make_question()
        result = evaluator.evaluate("A decorator wraps a function.", q)
        assert hasattr(result, "score")
        assert hasattr(result, "keywords_found")
        assert hasattr(result, "keywords_missed")
        assert hasattr(result, "keyword_score")
        assert hasattr(result, "length_score")
        assert hasattr(result, "relevance_score")
        assert hasattr(result, "strengths")
        assert hasattr(result, "improvements")
        assert hasattr(result, "model_answer_hint")
        assert hasattr(result, "confidence")


# ══════════════════════════════════════════════════════════════════════════════
# ANSWER EVALUATOR — CONVENIENCE FUNCTION
# ══════════════════════════════════════════════════════════════════════════════


class TestEvaluateAnswerConvenience:
    """Tests for the evaluate_answer() convenience function."""

    def test_returns_dict_with_expected_keys(self):
        """evaluate_answer should return dict with score, strengths, gaps, etc."""
        result = evaluate_answer(
            question_text="What is a Python list?",
            answer_text="A list is a mutable ordered collection in Python.",
            expected_keywords=["mutable", "ordered", "collection", "index"],
        )
        assert "score" in result
        assert "strengths" in result
        assert "gaps" in result
        assert "model_answer_hint" in result
        assert "acknowledgment" in result
        assert "keywords_found" in result
        assert "keywords_missed" in result

    def test_score_is_integer(self):
        """Score from convenience function should be an integer (rounded)."""
        result = evaluate_answer(
            question_text="What is REST?",
            answer_text="REST is an architectural style for APIs.",
            expected_keywords=["REST", "HTTP", "stateless"],
        )
        assert isinstance(result["score"], int)

    def test_acknowledgment_varies_by_score(self):
        """Acknowledgment message should match the score level."""
        # High score answer
        high_result = evaluate_answer(
            question_text="What is polymorphism?",
            answer_text=(
                "Polymorphism is a fundamental OOP concept that allows objects of "
                "different classes to be treated as objects of a common base class. "
                "There are compile-time polymorphism (method overloading) and "
                "runtime polymorphism (method overriding). Duck typing in Python "
                "provides polymorphism without explicit inheritance."
            ),
            expected_keywords=["polymorphism", "OOP", "overloading", "overriding", "inheritance", "duck typing"],
        )
        # Low score answer
        low_result = evaluate_answer(
            question_text="What is polymorphism?",
            answer_text="I don't know.",
            expected_keywords=["polymorphism", "OOP", "overloading", "overriding", "inheritance"],
        )
        # Acknowledgments should differ
        assert high_result["acknowledgment"] != low_result["acknowledgment"]

    def test_empty_answer(self):
        """Empty answer should score 0."""
        result = evaluate_answer(
            question_text="Explain anything.",
            answer_text="",
            expected_keywords=["something"],
        )
        assert result["score"] == 0

    def test_no_keywords(self):
        """No expected keywords should still produce valid result."""
        result = evaluate_answer(
            question_text="Tell me about yourself.",
            answer_text="I am a software developer with experience in Python.",
            expected_keywords=[],
        )
        assert 0 <= result["score"] <= 10

    def test_difficulty_parameter(self):
        """Difficulty parameter should affect length expectations."""
        short_answer = "Decorators wrap functions."
        result_easy = evaluate_answer(
            question_text="What are decorators?",
            answer_text=short_answer,
            expected_keywords=["decorators", "functions"],
            difficulty="easy",
        )
        result_hard = evaluate_answer(
            question_text="What are decorators?",
            answer_text=short_answer,
            expected_keywords=["decorators", "functions"],
            difficulty="hard",
        )
        # Same answer should score lower on hard difficulty (higher length expectations)
        # (or at least not score higher)
        assert result_easy["score"] >= result_hard["score"]


# ══════════════════════════════════════════════════════════════════════════════
# ANSWER EVALUATOR — BATCH & OVERALL SCORING
# ══════════════════════════════════════════════════════════════════════════════


class TestAnswerEvaluatorBatch:
    """Tests for batch evaluation and overall scoring."""

    @pytest.fixture
    def evaluator(self):
        return AnswerEvaluator()

    def _make_question(self, keywords, difficulty="medium"):
        return Question(
            id="q", text="Q?", topic="t", difficulty=difficulty,
            category="python", question_type="technical",
            expected_keywords=keywords, model_answer_hint="hint",
        )

    def test_batch_evaluate_length_mismatch_raises(self, evaluator):
        """evaluate_batch should raise if answers/questions count mismatch."""
        questions = [self._make_question(["kw1"])]
        with pytest.raises(ValueError):
            evaluator.evaluate_batch(["a1", "a2"], questions)

    def test_batch_evaluate_returns_list(self, evaluator):
        """evaluate_batch should return list of EvaluationResults."""
        questions = [
            self._make_question(["python"]),
            self._make_question(["react"]),
        ]
        results = evaluator.evaluate_batch(
            ["Python is great", "React is a library"],
            questions,
        )
        assert len(results) == 2
        assert all(isinstance(r, EvaluationResult) for r in results)

    def test_overall_score_calculation(self, evaluator):
        """get_overall_score should correctly aggregate results."""
        results = [
            EvaluationResult(score=8.0, keywords_found=["a", "b"], keywords_missed=["c"]),
            EvaluationResult(score=6.0, keywords_found=["x"], keywords_missed=["y", "z"]),
            EvaluationResult(score=4.0, keywords_found=[], keywords_missed=["m", "n"]),
        ]
        overall = evaluator.get_overall_score(results)
        assert overall["overall"] == 6.0  # (8+6+4)/3
        assert overall["highest"] == 8.0
        assert overall["lowest"] == 4.0
        assert overall["count"] == 3
        assert overall["strong_answers"] == 1  # Only 8.0 >= 7
        assert overall["weak_answers"] == 0  # 4.0 is not < 4.0

    def test_overall_score_empty_list(self, evaluator):
        """Empty results list should return zeros."""
        overall = evaluator.get_overall_score([])
        assert overall["overall"] == 0.0
        assert overall["count"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# FEEDBACK GENERATOR — OUTPUT FORMAT
# ══════════════════════════════════════════════════════════════════════════════


class TestFeedbackGeneratorFormat:
    """Tests for feedback generator output structure and content."""

    @pytest.fixture
    def generator(self):
        return FeedbackGenerator()

    def test_generate_feedback_returns_all_keys(self, generator):
        """Feedback dict should contain all expected sections."""
        result = EvaluationResult(
            score=7.5,
            keywords_found=["python", "django"],
            keywords_missed=["flask"],
            keyword_score=8.0,
            length_score=7.0,
            relevance_score=7.0,
            strengths=["Good coverage of frameworks"],
            improvements=["Mention Flask for completeness"],
            model_answer_hint="Include Flask and Django comparison.",
            confidence=0.8,
        )
        feedback = generator.generate_feedback(result)
        expected_keys = [
            "summary", "encouragement", "strengths",
            "improvements", "model_answer_hint", "score_breakdown",
        ]
        for key in expected_keys:
            assert key in feedback, f"Missing key: {key}"
            assert isinstance(feedback[key], str)

    def test_excellent_tier_feedback(self, generator):
        """Score >= 8.5 should get excellent-tier messages."""
        result = EvaluationResult(
            score=9.2,
            keywords_found=["a", "b", "c", "d", "e"],
            keywords_missed=[],
            keyword_score=10.0,
            length_score=9.0,
            relevance_score=9.0,
            strengths=["Comprehensive answer"],
            improvements=[],
            model_answer_hint="",
            confidence=0.9,
        )
        feedback = generator.generate_feedback(result)
        assert "9.2/10" in feedback["summary"]
        # Should have positive tone
        assert any(word in feedback["encouragement"].lower()
                   for word in ["outstanding", "excellent", "impressive", "great", "superb"])

    def test_low_score_tier_feedback(self, generator):
        """Score < 3.0 should get improvement-focused messages."""
        result = EvaluationResult(
            score=2.0,
            keywords_found=[],
            keywords_missed=["a", "b", "c"],
            keyword_score=1.0,
            length_score=2.0,
            relevance_score=2.0,
            strengths=[],
            improvements=["Study core concepts"],
            model_answer_hint="Focus on fundamentals.",
            confidence=0.5,
        )
        feedback = generator.generate_feedback(result)
        assert "2.0/10" in feedback["summary"]

    def test_generate_short_feedback(self, generator):
        """Short feedback should be a single concise string."""
        result = EvaluationResult(
            score=6.5,
            keywords_found=["python"],
            keywords_missed=["django"],
            confidence=0.7,
        )
        short = generator.generate_short_feedback(result)
        assert isinstance(short, str)
        assert "6.5/10" in short

    def test_generate_interview_summary_no_results(self, generator):
        """Empty results list should return N/A summary."""
        summary = generator.generate_interview_summary([])
        assert summary["overall_score"] == "N/A"
        assert "No" in summary["summary"] or "no" in summary["summary"]

    def test_generate_interview_summary_with_results(self, generator):
        """Full summary with real results should have all sections."""
        results = [
            EvaluationResult(score=8.0, keywords_found=["a"], keywords_missed=["b"]),
            EvaluationResult(score=6.0, keywords_found=["c"], keywords_missed=["d"]),
            EvaluationResult(score=4.0, keywords_found=[], keywords_missed=["e", "f"]),
        ]
        questions = [
            Question(id="1", text="Q1?", topic="t", difficulty="easy",
                     category="python", question_type="technical",
                     expected_keywords=["a", "b"]),
            Question(id="2", text="Q2?", topic="t", difficulty="medium",
                     category="sql", question_type="technical",
                     expected_keywords=["c", "d"]),
            Question(id="3", text="Q3?", topic="t", difficulty="hard",
                     category="aws", question_type="technical",
                     expected_keywords=["e", "f"]),
        ]
        summary = generator.generate_interview_summary(results, questions)
        assert "6.0/10" in summary["overall_score"]  # (8+6+4)/3 = 6.0
        assert "performance_level" in summary
        assert "summary" in summary
        assert "strengths_summary" in summary
        assert "improvement_areas" in summary
        assert "recommendation" in summary
        assert "score_distribution" in summary

    def test_convenience_generate_feedback(self):
        """Convenience generate_feedback function should work with dict input."""
        result_dict = {
            "score": 7.0,
            "keywords_found": ["python"],
            "keywords_missed": ["django"],
            "keyword_score": 7.0,
            "length_score": 6.0,
            "relevance_score": 7.0,
            "strengths": ["Good"],
            "improvements": ["Add more"],
            "model_answer_hint": "Hint text",
            "confidence": 0.7,
        }
        feedback = generate_feedback(result_dict, question_text="Test?")
        assert isinstance(feedback, dict)
        assert "summary" in feedback


# ══════════════════════════════════════════════════════════════════════════════
# QUESTION BANK — SANITY CHECKS
# ══════════════════════════════════════════════════════════════════════════════


class TestQuestionBankSanity:
    """Basic sanity checks on the question bank."""

    @pytest.fixture
    def bank(self):
        return get_question_bank()

    def test_bank_has_questions(self, bank):
        """Question bank should have a significant number of questions."""
        assert bank.total_questions >= 100

    def test_bank_has_multiple_categories(self, bank):
        """Should cover many technology categories."""
        stats = bank.get_stats()
        assert len(stats["by_category"]) >= 8

    def test_bank_has_all_difficulties(self, bank):
        """Should have easy, medium, and hard questions."""
        easy = bank.get_by_difficulty("easy")
        medium = bank.get_by_difficulty("medium")
        hard = bank.get_by_difficulty("hard")
        assert len(easy) > 0
        assert len(medium) > 0
        assert len(hard) > 0

    def test_bank_has_behavioral_questions(self, bank):
        """Should have behavioral/HR questions."""
        behavioral = bank.get_by_category("behavioral")
        assert len(behavioral) >= 10

    def test_all_questions_have_required_fields(self, bank):
        """Every question should have id, text, difficulty, category, expected_keywords."""
        for q_id, question in bank._questions.items():
            assert question.id, f"Question missing id"
            assert question.text, f"Question {q_id} missing text"
            assert question.difficulty in ("easy", "medium", "hard"), \
                f"Question {q_id} invalid difficulty: {question.difficulty}"
            assert question.category, f"Question {q_id} missing category"
            assert isinstance(question.expected_keywords, list), \
                f"Question {q_id} expected_keywords not a list"

    def test_filter_questions_by_category(self, bank):
        """Filtering by category should return only matching questions."""
        python_qs = bank.filter_questions(categories=["python"])
        assert all(q.category == "python" for q in python_qs)
        assert len(python_qs) > 0

    def test_filter_questions_by_difficulty(self, bank):
        """Filtering by difficulty should return only matching questions."""
        easy_qs = bank.filter_questions(difficulties=["easy"])
        assert all(q.difficulty == "easy" for q in easy_qs)

    def test_random_selection_respects_count(self, bank):
        """random_selection should return at most n questions."""
        selection = bank.random_selection(n=5)
        assert len(selection) == 5
