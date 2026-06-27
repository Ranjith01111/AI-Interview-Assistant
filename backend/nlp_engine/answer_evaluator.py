"""
Answer Evaluator v2 — Enhanced scoring with synonym/concept matching,
n-gram phrase detection, answer structure analysis, partial credit for
related concepts, and communication quality scoring.

100% offline. No LLMs. No API calls.
Uses: scikit-learn, numpy, re, collections (all in requirements.txt)

IMPROVEMENTS OVER v1:
1. Synonym/Concept Matching — Tech synonym dictionary expands keyword coverage
2. N-gram Phrase Matching — Multi-word phrases scored as units
3. Answer Structure Scoring — Rewards STAR method, pros/cons, numbered steps
4. Partial Credit for Related Concepts — Related but non-exact terms earn partial credit
5. Communication Quality Score — Evaluates clarity, coherence, professional language

BACKWARD COMPATIBLE: evaluate_answer() signature unchanged.
"""

import re
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter

import numpy as np

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Try relative import (when used as a module), fallback for standalone
try:
    from .question_bank import Question
except ImportError:
    # Standalone usage — define a minimal Question dataclass
    @dataclass
    class Question:
        id: str
        text: str
        topic: str
        difficulty: str
        category: str
        question_type: str
        expected_keywords: List[str] = field(default_factory=list)
        model_answer_hint: str = ""
        follow_up: str = ""


# ══════════════════════════════════════════════════════════════════════════════
# EVALUATION RESULT
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class EvaluationResult:
    """Complete evaluation result for a single answer."""
    score: float  # 0.0 - 10.0
    keywords_found: List[str] = field(default_factory=list)
    keywords_missed: List[str] = field(default_factory=list)
    keyword_score: float = 0.0
    length_score: float = 0.0
    relevance_score: float = 0.0
    structure_score: float = 0.0       # NEW: answer structure quality
    communication_score: float = 0.0   # NEW: communication quality
    concept_score: float = 0.0         # NEW: concept/synonym matching
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    model_answer_hint: str = ""
    confidence: float = 0.0


# ══════════════════════════════════════════════════════════════════════════════
# SCORING WEIGHTS (v2 — rebalanced)
# ══════════════════════════════════════════════════════════════════════════════
#
# v1 weights: KEYWORD=0.50, LENGTH=0.20, RELEVANCE=0.30
# v2 weights: reduce keyword dependency, add structure + communication
#
KEYWORD_WEIGHT = 0.30       # Reduced from 0.50 — less keyword-dependent
CONCEPT_WEIGHT = 0.15       # NEW: synonym/related concept matching
LENGTH_WEIGHT = 0.10        # Reduced from 0.20 — less emphasis on length alone
RELEVANCE_WEIGHT = 0.20     # Reduced from 0.30 — TF-IDF still important
STRUCTURE_WEIGHT = 0.15     # NEW: answer structure quality
COMMUNICATION_WEIGHT = 0.10 # NEW: communication clarity and coherence

# Weights must sum to 1.0
assert abs(KEYWORD_WEIGHT + CONCEPT_WEIGHT + LENGTH_WEIGHT +
           RELEVANCE_WEIGHT + STRUCTURE_WEIGHT + COMMUNICATION_WEIGHT - 1.0) < 0.001


# ══════════════════════════════════════════════════════════════════════════════
# LENGTH THRESHOLDS
# ══════════════════════════════════════════════════════════════════════════════
MIN_WORDS_EASY = 20
MIN_WORDS_MEDIUM = 40
MIN_WORDS_HARD = 60
IDEAL_WORDS_EASY = 80
IDEAL_WORDS_MEDIUM = 150
IDEAL_WORDS_HARD = 250
MAX_WORDS_PENALTY = 500


# ══════════════════════════════════════════════════════════════════════════════
# TECH SYNONYM DICTIONARY (Improvement #1)
# ══════════════════════════════════════════════════════════════════════════════
# Bidirectional: if "async/await" is expected, "asynchronous" in the answer matches.
# Each key maps to a set of equivalent terms.

TECH_SYNONYMS = {
    # Async/Concurrency
    "async": {"asynchronous", "async/await", "asyncio", "non-blocking", "event-driven"},
    "asynchronous": {"async", "async/await", "asyncio", "non-blocking"},
    "async/await": {"asynchronous", "async", "asyncio", "coroutine"},
    "concurrency": {"concurrent", "parallelism", "parallel", "multithreading", "multiprocessing"},
    "multithreading": {"threading", "threads", "multi-threaded", "concurrent"},
    "event loop": {"asyncio", "event-driven", "non-blocking i/o"},

    # Databases
    "database": {"db", "datastore", "data store", "rdbms", "dbms"},
    "db": {"database", "datastore"},
    "sql": {"structured query language", "relational database", "rdbms"},
    "nosql": {"non-relational", "document store", "mongodb", "dynamodb"},
    "orm": {"object-relational mapping", "sqlalchemy", "sequelize", "hibernate"},
    "index": {"indexing", "b-tree", "database index", "query optimization"},
    "normalization": {"normal form", "1nf", "2nf", "3nf", "database design"},
    "denormalization": {"denormalized", "read optimization"},
    "acid": {"atomicity", "consistency", "isolation", "durability", "transaction"},
    "transaction": {"acid", "commit", "rollback", "atomic operation"},

    # Caching
    "caching": {"cache", "redis", "memcached", "in-memory", "memoization", "memoize"},
    "cache": {"caching", "redis", "memcached", "in-memory store"},
    "redis": {"cache", "caching", "in-memory database", "key-value store"},
    "memoization": {"memoize", "cache", "caching", "lru_cache"},

    # Containers & Orchestration
    "kubernetes": {"k8s", "container orchestration", "kube"},
    "k8s": {"kubernetes", "container orchestration"},
    "docker": {"container", "containerization", "dockerfile"},
    "container": {"docker", "containerization", "isolated environment"},
    "microservices": {"micro-services", "microservice architecture", "service-oriented"},

    # CI/CD
    "ci/cd": {"continuous integration", "continuous deployment", "continuous delivery", "pipeline"},
    "continuous integration": {"ci", "ci/cd", "automated testing", "build pipeline"},
    "continuous deployment": {"cd", "ci/cd", "automated deployment"},
    "devops": {"ci/cd", "infrastructure as code", "automation"},

    # Design Patterns
    "dependency injection": {"di", "inversion of control", "ioc", "constructor injection"},
    "singleton": {"singleton pattern", "single instance"},
    "factory": {"factory pattern", "factory method", "abstract factory"},
    "observer": {"observer pattern", "pub/sub", "publish-subscribe", "event-driven"},
    "decorator": {"decorator pattern", "wrapper", "@decorator"},
    "strategy": {"strategy pattern", "behavioral pattern"},
    "mvc": {"model-view-controller", "model view controller"},
    "solid": {"single responsibility", "open/closed", "liskov", "interface segregation", "dependency inversion"},

    # Architecture
    "rest": {"restful", "rest api", "representational state transfer"},
    "api": {"application programming interface", "endpoint", "rest api", "graphql"},
    "graphql": {"graph query language", "api query language"},
    "monolith": {"monolithic", "monolithic architecture"},
    "load balancing": {"load balancer", "horizontal scaling", "nginx", "haproxy"},
    "scalability": {"scaling", "horizontal scaling", "vertical scaling", "scale out"},
    "horizontal scaling": {"scale out", "adding instances", "load balancing"},
    "vertical scaling": {"scale up", "bigger machine", "more resources"},

    # Python-specific
    "decorator": {"@decorator", "wrapper function", "functools.wraps"},
    "generator": {"yield", "generator function", "lazy evaluation", "iterator"},
    "list comprehension": {"listcomp", "comprehension", "[x for x in ...]"},
    "gil": {"global interpreter lock", "python threading limitation"},
    "global interpreter lock": {"gil", "cpython limitation"},
    "virtual environment": {"venv", "virtualenv", "isolated environment"},
    "type hints": {"type annotations", "typing", "mypy", "static typing"},
    "metaclass": {"meta-class", "__metaclass__", "type()"},

    # JavaScript/TypeScript
    "closure": {"lexical scope", "enclosed variable", "function scope"},
    "promise": {"async", "then/catch", "future", "deferred"},
    "callback": {"callback function", "higher-order function", "event handler"},
    "prototype": {"prototypal inheritance", "__proto__", "prototype chain"},
    "hoisting": {"variable hoisting", "function hoisting"},
    "typescript": {"ts", "typed javascript", "static typing"},

    # Frontend
    "virtual dom": {"vdom", "reconciliation", "diffing algorithm"},
    "state management": {"redux", "zustand", "context api", "vuex", "global state"},
    "component": {"react component", "ui component", "reusable component"},
    "hooks": {"react hooks", "usestate", "useeffect", "custom hooks"},

    # Security
    "authentication": {"auth", "authn", "login", "identity verification"},
    "authorization": {"authz", "permissions", "access control", "rbac"},
    "jwt": {"json web token", "token-based auth", "bearer token"},
    "oauth": {"oauth2", "oauth 2.0", "authorization framework"},
    "encryption": {"encrypt", "aes", "rsa", "cryptography", "tls", "ssl"},
    "hashing": {"hash", "bcrypt", "sha", "md5", "password hashing"},
    "xss": {"cross-site scripting", "script injection"},
    "csrf": {"cross-site request forgery"},
    "sql injection": {"sqli", "injection attack", "parameterized queries"},

    # Testing
    "unit testing": {"unit test", "unittest", "pytest", "jest", "test case"},
    "integration testing": {"integration test", "end-to-end", "e2e"},
    "tdd": {"test-driven development", "test first", "red-green-refactor"},
    "mocking": {"mock", "stub", "test double", "fake", "spy"},

    # Cloud/Infrastructure
    "aws": {"amazon web services", "cloud", "ec2", "s3", "lambda"},
    "serverless": {"lambda", "cloud functions", "faas", "function as a service"},
    "infrastructure as code": {"iac", "terraform", "cloudformation", "pulumi"},

    # Data Structures
    "hash table": {"hash map", "dictionary", "dict", "hashmap", "associative array"},
    "linked list": {"singly linked", "doubly linked", "node-based"},
    "binary tree": {"bst", "binary search tree", "tree data structure"},
    "graph": {"directed graph", "undirected graph", "adjacency list", "adjacency matrix"},
    "queue": {"fifo", "first-in-first-out", "message queue"},
    "stack": {"lifo", "last-in-first-out", "call stack"},
    "heap": {"priority queue", "min-heap", "max-heap", "heapq"},

    # Algorithms
    "big o": {"time complexity", "space complexity", "algorithmic complexity", "o(n)"},
    "time complexity": {"big o", "algorithmic efficiency", "performance"},
    "dynamic programming": {"dp", "memoization", "optimal substructure", "overlapping subproblems"},
    "recursion": {"recursive", "base case", "recursive function", "call stack"},
    "sorting": {"sort", "quicksort", "mergesort", "bubble sort", "timsort"},

    # General Software Engineering
    "refactoring": {"refactor", "code cleanup", "restructuring", "technical debt"},
    "technical debt": {"tech debt", "code debt", "accumulated shortcuts"},
    "code review": {"peer review", "pull request review", "cr"},
    "agile": {"scrum", "sprint", "kanban", "iterative development"},
    "version control": {"git", "source control", "vcs"},
    "git": {"version control", "source control", "repository"},

    # Object-Oriented
    "object-oriented": {"oop", "oo", "object oriented programming"},
    "inheritance": {"class inheritance", "subclass", "extends", "derived class"},
    "polymorphism": {"method overriding", "duck typing", "interface"},
    "encapsulation": {"data hiding", "private", "access modifiers", "information hiding"},
    "abstraction": {"abstract class", "interface", "abstract method"},
    "composition": {"has-a relationship", "object composition", "prefer composition"},

    # Abbreviations
    "application": {"app", "software"},
    "configuration": {"config", "settings", "env"},
    "repository": {"repo", "codebase"},
    "function": {"func", "fn", "method", "subroutine"},
    "implementation": {"impl", "realization"},
    "infrastructure": {"infra", "platform"},
}

# Build a reverse-lookup: for each term, what groups does it belong to?
_SYNONYM_GROUPS: Dict[str, Set[str]] = {}

def _build_synonym_index():
    """Build the reverse-lookup synonym index at module load time."""
    for key, synonyms in TECH_SYNONYMS.items():
        all_terms = {key.lower()} | {s.lower() for s in synonyms}
        for term in all_terms:
            if term not in _SYNONYM_GROUPS:
                _SYNONYM_GROUPS[term] = set()
            _SYNONYM_GROUPS[term].update(all_terms)

_build_synonym_index()


# ══════════════════════════════════════════════════════════════════════════════
# RELATED CONCEPTS MAP (Improvement #4)
# ══════════════════════════════════════════════════════════════════════════════
# Maps keywords to related (but not equivalent) concepts that deserve partial credit.
# Score: 0.5x credit for mentioning a related concept.

RELATED_CONCEPTS = {
    "caching": ["redis", "memcached", "cdn", "performance", "latency", "response time"],
    "redis": ["caching", "pub/sub", "session store", "message broker"],
    "database": ["storage", "persistence", "data layer", "repository pattern"],
    "indexing": ["query optimization", "performance", "b-tree", "search"],
    "scalability": ["load balancing", "caching", "microservices", "horizontal scaling", "sharding"],
    "load balancing": ["nginx", "scalability", "high availability", "fault tolerance"],
    "microservices": ["api gateway", "service discovery", "event-driven", "docker", "kubernetes"],
    "docker": ["containerization", "kubernetes", "deployment", "isolation"],
    "kubernetes": ["docker", "orchestration", "scaling", "deployment", "pods"],
    "testing": ["quality", "reliability", "bugs", "coverage", "ci/cd"],
    "security": ["authentication", "authorization", "encryption", "vulnerability"],
    "authentication": ["security", "jwt", "oauth", "session", "login"],
    "rest api": ["http", "endpoints", "json", "status codes", "crud"],
    "polymorphism": ["inheritance", "interfaces", "abstraction", "oop"],
    "inheritance": ["polymorphism", "composition", "code reuse", "oop"],
    "design patterns": ["solid", "clean code", "architecture", "maintainability"],
    "async": ["performance", "non-blocking", "scalability", "i/o bound"],
    "garbage collection": ["memory management", "reference counting", "gc"],
    "event loop": ["async", "callbacks", "non-blocking", "concurrency"],
    "closure": ["scope", "functions", "encapsulation", "state"],
    "hooks": ["state management", "lifecycle", "react", "functional components"],
    "virtual dom": ["performance", "rendering", "reconciliation", "react"],
    "sql injection": ["security", "parameterized queries", "input validation"],
    "normalization": ["data integrity", "redundancy", "database design"],
    "acid": ["reliability", "data integrity", "transactions", "consistency"],
    "big o": ["performance", "optimization", "efficiency", "algorithm design"],
    "dynamic programming": ["optimization", "recursion", "efficiency", "algorithms"],
    "git": ["collaboration", "branching", "merging", "version history"],
    "agile": ["collaboration", "iterations", "feedback", "adaptability"],
    "refactoring": ["clean code", "maintainability", "technical debt", "readability"],
    "solid": ["maintainability", "clean architecture", "design principles"],
    "tdd": ["testing", "design", "refactoring", "quality", "confidence"],
    "ci/cd": ["automation", "deployment", "testing", "devops", "reliability"],
    "serverless": ["scalability", "cost", "event-driven", "managed infrastructure"],
}


# ══════════════════════════════════════════════════════════════════════════════
# ANSWER STRUCTURE PATTERNS (Improvement #3)
# ══════════════════════════════════════════════════════════════════════════════

STRUCTURE_PATTERNS = {
    "star_method": {
        "description": "STAR method (Situation, Task, Action, Result)",
        "patterns": [
            r'\b(situation|context|background)\b.*\b(task|challenge|problem|goal)\b.*\b(action|approach|solution|did|implemented)\b.*\b(result|outcome|impact|achieved)\b',
        ],
        "keywords": [
            ["situation", "context", "background", "scenario"],
            ["task", "challenge", "problem", "objective", "goal"],
            ["action", "approach", "implemented", "developed", "built", "created"],
            ["result", "outcome", "impact", "achieved", "improved", "reduced"],
        ],
        "min_keyword_groups": 3,  # Need at least 3 of 4 groups
        "bonus": 2.0,
    },
    "numbered_steps": {
        "description": "Numbered steps / ordered approach",
        "patterns": [
            r'(?:^|\n)\s*(?:1[.):]|step\s*1)',  # At least starts with step 1
        ],
        "counter_pattern": r'(?:^|\n)\s*(?:\d+[.):]|step\s*\d+)',
        "min_count": 3,
        "bonus": 1.5,
    },
    "pros_cons": {
        "description": "Pros/Cons or Trade-off analysis",
        "patterns": [
            r'\b(pros?|advantages?|benefits?)\b.*\b(cons?|disadvantages?|drawbacks?|limitations?)\b',
            r'\b(trade-?offs?|on the other hand|however|conversely|whereas)\b',
        ],
        "bonus": 1.2,
    },
    "comparison": {
        "description": "Comparative analysis",
        "patterns": [
            r'\b(compared to|versus|vs\.?|unlike|in contrast|difference between)\b',
            r'\b(whereas|while|on one hand|alternatively)\b',
        ],
        "bonus": 1.0,
    },
    "example_driven": {
        "description": "Example-driven explanation",
        "patterns": [
            r'\b(for example|for instance|such as|e\.g\.)\b',
        ],
        "counter_pattern": r'\b(for example|for instance|such as|e\.g\.|consider)\b',
        "min_count": 2,
        "bonus": 1.0,
    },
    "definition_then_depth": {
        "description": "Definition → Explanation → Example flow",
        "patterns": [
            r'.{20,}\b(this means|in other words|to put it simply|essentially)\b.{20,}\b(for example|for instance|such as)\b',
        ],
        "bonus": 1.0,
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# COMMUNICATION QUALITY INDICATORS (Improvement #5)
# ══════════════════════════════════════════════════════════════════════════════

FILLER_PATTERNS = [
    r'\b(um+|uh+|hmm+|ahh+)\b',
    r'\b(like|basically|actually|literally)\b(?!\s+(?:a |the |this |that |an ))',  # Smarter: "like" as filler vs "like a"
    r'\b(you know|i mean|so yeah|kind of|sort of)\b',
    r'\b(i think maybe|i\'m not sure|i don\'t know|no idea)\b',
    r'\b(and stuff|things like that|and whatnot|blah)\b',
]

HEDGING_PATTERNS = [
    r'\b(maybe|perhaps|possibly|i guess|i suppose|might be|could be)\b',
    r'\b(not entirely sure|don\'t remember exactly|something like)\b',
]

PROFESSIONAL_LANGUAGE = [
    r'\b(specifically|particularly|fundamentally|essentially)\b',
    r'\b(consequently|therefore|furthermore|moreover|additionally)\b',
    r'\b(implement|architecture|optimize|design|pattern|principle)\b',
    r'\b(ensures?|enables?|facilitates?|leverages?|provides?)\b',
    r'\b(scalab|maintain|modular|robust|efficient|performan)\w*\b',
]

TRANSITION_PHRASES = [
    r'\b(first|second|third|finally|in addition|moreover)\b',
    r'\b(however|on the other hand|that said|nevertheless)\b',
    r'\b(as a result|because of this|this leads to|which means)\b',
    r'\b(in summary|to summarize|in conclusion|overall)\b',
    r'\b(building on that|related to this|another aspect)\b',
]

QUALITY_INDICATORS = [
    r'\b(for example|such as|specifically|in particular)\b',
    r'\b(because|therefore|consequently|as a result|this means)\b',
    r'\b(first|second|third|additionally|furthermore|moreover)\b',
    r'\b(trade-off|advantage|disadvantage|comparison|versus)\b',
    r'\b(in production|in practice|real-world|at scale)\b',
]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN EVALUATOR CLASS
# ══════════════════════════════════════════════════════════════════════════════

class AnswerEvaluatorV2:
    """
    Enhanced Answer Evaluator with:
    - Synonym/concept matching
    - N-gram phrase matching
    - Answer structure scoring
    - Partial credit for related concepts
    - Communication quality scoring
    """

    def __init__(self):
        if HAS_SKLEARN:
            self._vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=5000,
                ngram_range=(1, 3),  # Extended to trigrams for phrase matching
                sublinear_tf=True,
            )
        else:
            self._vectorizer = None

    def evaluate(
        self,
        answer: str,
        question: Question,
        strict: bool = False,
    ) -> EvaluationResult:
        """
        Evaluate an answer against a question's expected criteria.

        Args:
            answer: The candidate's answer text
            question: The Question object with expected_keywords
            strict: If True, use stricter scoring thresholds

        Returns:
            EvaluationResult with detailed breakdown
        """
        if not answer or not answer.strip():
            return EvaluationResult(
                score=0.0,
                keywords_missed=question.expected_keywords.copy(),
                improvements=["No answer was provided. Try to give a detailed response."],
                model_answer_hint=question.model_answer_hint,
                confidence=1.0,
            )

        # Normalize the answer
        answer_clean = self._normalize_text(answer)
        answer_lower = answer_clean.lower()

        # ── 1. Keyword Scoring (with synonym expansion) ──────────────
        keyword_result = self._score_keywords_v2(
            answer_lower, question.expected_keywords
        )

        # ── 2. Concept/Synonym Scoring (partial credit) ──────────────
        concept_result = self._score_concepts(
            answer_lower, question.expected_keywords
        )

        # ── 3. Length Scoring ─────────────────────────────────────────
        length_result = self._score_length(answer_clean, question.difficulty)

        # ── 4. Relevance Scoring (TF-IDF + n-gram phrases) ───────────
        relevance_result = self._score_relevance_v2(
            answer_clean, question.text, question.model_answer_hint
        )

        # ── 5. Structure Scoring ─────────────────────────────────────
        structure_result = self._score_structure(answer_clean, question)

        # ── 6. Communication Quality Scoring ─────────────────────────
        communication_result = self._score_communication(answer_clean)

        # ── Calculate weighted final score ────────────────────────────
        raw_score = (
            keyword_result["score"] * KEYWORD_WEIGHT +
            concept_result["score"] * CONCEPT_WEIGHT +
            length_result["score"] * LENGTH_WEIGHT +
            relevance_result["score"] * RELEVANCE_WEIGHT +
            structure_result["score"] * STRUCTURE_WEIGHT +
            communication_result["score"] * COMMUNICATION_WEIGHT
        )

        # Apply quality modifier (smaller role now — structure/communication handle this)
        quality_modifier = self._calculate_quality_modifier(answer_clean)
        final_score = max(0.0, min(10.0, raw_score + quality_modifier * 0.5))

        # Round to 1 decimal
        final_score = round(final_score, 1)

        # Generate strengths and improvements
        strengths = self._identify_strengths(
            keyword_result, concept_result, length_result,
            relevance_result, structure_result, communication_result,
            answer_clean
        )
        improvements = self._identify_improvements(
            keyword_result, concept_result, length_result,
            relevance_result, structure_result, communication_result,
            answer_clean, question
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            keyword_result, concept_result, length_result, answer_clean
        )

        return EvaluationResult(
            score=final_score,
            keywords_found=keyword_result["found"],
            keywords_missed=keyword_result["missed"],
            keyword_score=round(keyword_result["score"], 1),
            length_score=round(length_result["score"], 1),
            relevance_score=round(relevance_result["score"], 1),
            structure_score=round(structure_result["score"], 1),
            communication_score=round(communication_result["score"], 1),
            concept_score=round(concept_result["score"], 1),
            strengths=strengths,
            improvements=improvements,
            model_answer_hint=question.model_answer_hint,
            confidence=confidence,
        )

    def evaluate_batch(
        self,
        answers: List[str],
        questions: List[Question],
    ) -> List[EvaluationResult]:
        """Evaluate multiple answers at once."""
        if len(answers) != len(questions):
            raise ValueError("Number of answers must match number of questions")
        return [
            self.evaluate(answer, question)
            for answer, question in zip(answers, questions)
        ]

    def get_overall_score(self, results: List[EvaluationResult]) -> Dict:
        """Calculate overall interview score from multiple evaluations."""
        if not results:
            return {"overall": 0.0, "count": 0}

        scores = [r.score for r in results]
        total_found = sum(len(r.keywords_found) for r in results)
        total_expected = total_found + sum(len(r.keywords_missed) for r in results)

        return {
            "overall": round(sum(scores) / len(scores), 1),
            "highest": max(scores),
            "lowest": min(scores),
            "count": len(results),
            "keyword_coverage": round(
                (total_found / max(total_expected, 1)) * 100, 1
            ),
            "strong_answers": sum(1 for s in scores if s >= 7.0),
            "weak_answers": sum(1 for s in scores if s < 4.0),
            "avg_structure": round(
                sum(r.structure_score for r in results) / len(results), 1
            ),
            "avg_communication": round(
                sum(r.communication_score for r in results) / len(results), 1
            ),
        }

    # ══════════════════════════════════════════════════════════════════════════
    # KEYWORD SCORING (Enhanced with Synonyms — Improvement #1)
    # ══════════════════════════════════════════════════════════════════════════

    def _score_keywords_v2(
        self, answer_lower: str, expected_keywords: List[str]
    ) -> Dict:
        """
        Score based on keyword matching WITH synonym expansion.
        A keyword is 'found' if either:
        - The exact keyword (or basic variation) is present
        - A known synonym of that keyword is present in the answer
        """
        found = []
        missed = []
        synonym_matches = []  # Track which matched via synonym

        for keyword in expected_keywords:
            keyword_lower = keyword.lower()

            # Check direct match first
            if self._keyword_present(answer_lower, keyword_lower):
                found.append(keyword)
            # Check synonym match
            elif self._synonym_match(answer_lower, keyword_lower):
                found.append(keyword)
                synonym_matches.append(keyword)
            else:
                missed.append(keyword)

        # Calculate score
        if not expected_keywords:
            score = 5.0
        else:
            ratio = len(found) / len(expected_keywords)
            score = self._keyword_ratio_to_score(ratio)

        return {
            "score": score,
            "found": found,
            "missed": missed,
            "synonym_matches": synonym_matches,
        }

    def _synonym_match(self, text: str, keyword: str) -> bool:
        """Check if any synonym of the keyword appears in the text."""
        # Look up the keyword in our synonym groups
        keyword_lower = keyword.lower()

        # Direct lookup
        if keyword_lower in _SYNONYM_GROUPS:
            for synonym in _SYNONYM_GROUPS[keyword_lower]:
                if synonym != keyword_lower and self._term_in_text(text, synonym):
                    return True

        # Also check if the keyword matches any key in TECH_SYNONYMS
        if keyword_lower in TECH_SYNONYMS:
            for synonym in TECH_SYNONYMS[keyword_lower]:
                if self._term_in_text(text, synonym.lower()):
                    return True

        return False

    def _term_in_text(self, text: str, term: str) -> bool:
        """Check if a term appears in text (with word boundary awareness)."""
        if len(term) <= 2:
            # Short terms need word boundaries
            pattern = r'\b' + re.escape(term) + r'\b'
            return bool(re.search(pattern, text))
        return term in text

    # ══════════════════════════════════════════════════════════════════════════
    # CONCEPT SCORING (Partial Credit — Improvement #4)
    # ══════════════════════════════════════════════════════════════════════════

    def _score_concepts(
        self, answer_lower: str, expected_keywords: List[str]
    ) -> Dict:
        """
        Give partial credit for related concepts.
        If expected keyword is "caching" and answer mentions "Redis" or "performance",
        give 0.5x credit per related concept found.
        """
        if not expected_keywords:
            return {"score": 5.0, "related_found": [], "partial_credits": {}}

        partial_credits = {}
        related_found = []

        for keyword in expected_keywords:
            keyword_lower = keyword.lower()

            # Skip if keyword was already directly matched (handled in keyword scoring)
            if self._keyword_present(answer_lower, keyword_lower):
                continue
            if self._synonym_match(answer_lower, keyword_lower):
                continue

            # Check for related concepts
            related_terms = self._get_related_concepts(keyword_lower)
            matched_related = []

            for related_term in related_terms:
                if self._term_in_text(answer_lower, related_term.lower()):
                    matched_related.append(related_term)

            if matched_related:
                # Partial credit: 0.5 for each related concept, max 1.0 per keyword
                credit = min(1.0, len(matched_related) * 0.5)
                partial_credits[keyword] = {
                    "credit": credit,
                    "related_found": matched_related[:3],
                }
                related_found.extend(matched_related[:2])

        # Calculate score based on partial credits
        if not expected_keywords:
            score = 5.0
        else:
            total_credit = sum(pc["credit"] for pc in partial_credits.values())
            # Scale: partial credits can contribute up to max score
            max_possible = len(expected_keywords)
            ratio = total_credit / max_possible if max_possible > 0 else 0
            score = min(10.0, ratio * 12.0)  # Generous scaling for related concepts

        return {
            "score": score,
            "related_found": related_found,
            "partial_credits": partial_credits,
        }

    def _get_related_concepts(self, keyword: str) -> List[str]:
        """Get related (but not equivalent) concepts for a keyword."""
        related = []

        # Direct lookup in RELATED_CONCEPTS
        if keyword in RELATED_CONCEPTS:
            related.extend(RELATED_CONCEPTS[keyword])

        # Also check if any RELATED_CONCEPTS keys are synonyms of our keyword
        if keyword in _SYNONYM_GROUPS:
            for synonym in _SYNONYM_GROUPS[keyword]:
                if synonym in RELATED_CONCEPTS and synonym != keyword:
                    related.extend(RELATED_CONCEPTS[synonym])

        return list(set(related))[:10]  # Deduplicate, limit

    # ══════════════════════════════════════════════════════════════════════════
    # RELEVANCE SCORING (Enhanced with N-grams — Improvement #2)
    # ══════════════════════════════════════════════════════════════════════════

    def _score_relevance_v2(
        self, answer: str, question_text: str, model_hint: str
    ) -> Dict:
        """
        Enhanced relevance scoring:
        - TF-IDF with up to trigrams (catches multi-word phrases)
        - Explicit phrase matching bonus
        - Combined scoring
        """
        tfidf_score = self._score_tfidf_relevance(answer, question_text, model_hint)
        phrase_score = self._score_phrase_matching(answer, question_text, model_hint)

        # Blend: 60% TF-IDF, 40% phrase matching
        combined_score = tfidf_score["score"] * 0.6 + phrase_score["score"] * 0.4

        return {
            "score": combined_score,
            "tfidf_similarity": tfidf_score.get("similarity", 0),
            "phrases_matched": phrase_score.get("phrases_matched", []),
        }

    def _score_tfidf_relevance(
        self, answer: str, question_text: str, model_hint: str
    ) -> Dict:
        """TF-IDF cosine similarity scoring (improved from v1)."""
        if not HAS_SKLEARN or not model_hint:
            return self._fallback_relevance(answer, question_text, model_hint)

        try:
            reference = f"{question_text} {model_hint}"

            # Use trigrams for better phrase capture
            vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 3),
                sublinear_tf=True,
                max_features=8000,
            )
            tfidf_matrix = vectorizer.fit_transform([reference, answer])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

            # Better scaling: use a sigmoid-like curve instead of linear
            # This gives more credit for moderate similarity
            score = 10.0 * (1 - math.exp(-4.0 * similarity))
            score = max(0.0, min(10.0, score))

            return {"score": score, "similarity": float(similarity)}

        except Exception:
            return self._fallback_relevance(answer, question_text, model_hint)

    def _score_phrase_matching(
        self, answer: str, question_text: str, model_hint: str
    ) -> Dict:
        """
        N-gram phrase matching (Improvement #2).
        Extract important multi-word phrases from the model hint/question
        and check if they appear in the answer.
        """
        answer_lower = answer.lower()
        reference = f"{question_text} {model_hint}".lower()

        # Extract meaningful n-grams (2-grams and 3-grams) from reference
        reference_phrases = self._extract_meaningful_phrases(reference)
        answer_phrases = self._extract_meaningful_phrases(answer_lower)

        if not reference_phrases:
            return {"score": 5.0, "phrases_matched": []}

        # Check which reference phrases appear in the answer
        matched_phrases = []
        for phrase in reference_phrases:
            if phrase in answer_lower or phrase in answer_phrases:
                matched_phrases.append(phrase)

        # Score based on phrase coverage
        ratio = len(matched_phrases) / max(len(reference_phrases), 1)
        score = min(10.0, ratio * 15.0)  # Generous: 67% coverage → 10

        return {
            "score": max(0.0, score),
            "phrases_matched": matched_phrases[:10],
        }

    def _extract_meaningful_phrases(self, text: str) -> Set[str]:
        """Extract meaningful 2-gram and 3-gram phrases from text."""
        # Remove punctuation but keep hyphens
        clean = re.sub(r'[^\w\s\-]', ' ', text)
        words = clean.split()

        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can',
            'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them',
            'their', 'we', 'our', 'you', 'your', 'he', 'she', 'him', 'her',
            'not', 'no', 'so', 'if', 'then', 'than', 'as', 'from', 'into',
            'about', 'between', 'through', 'during', 'before', 'after',
            'which', 'what', 'where', 'when', 'how', 'who', 'whom',
            'each', 'every', 'all', 'both', 'few', 'more', 'most', 'other',
            'some', 'such', 'very', 'just', 'also', 'well', 'still',
        }

        phrases = set()

        # 2-grams
        for i in range(len(words) - 1):
            w1, w2 = words[i].lower(), words[i + 1].lower()
            if w1 not in stopwords and w2 not in stopwords:
                if len(w1) >= 3 and len(w2) >= 3:
                    phrases.add(f"{w1} {w2}")

        # 3-grams (allow one stopword in the middle)
        for i in range(len(words) - 2):
            w1, w2, w3 = words[i].lower(), words[i + 1].lower(), words[i + 2].lower()
            if w1 not in stopwords and w3 not in stopwords:
                if len(w1) >= 3 and len(w3) >= 3:
                    phrases.add(f"{w1} {w2} {w3}")

        return phrases

    def _fallback_relevance(
        self, answer: str, question_text: str, model_hint: str
    ) -> Dict:
        """Fallback relevance scoring using word overlap."""
        reference_words = set(
            re.findall(r'\b\w{3,}\b', f"{question_text} {model_hint}".lower())
        )
        answer_words = set(re.findall(r'\b\w{3,}\b', answer.lower()))

        stopwords = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'had', 'her', 'was', 'one', 'our', 'out', 'has',
            'have', 'been', 'with', 'this', 'that', 'from', 'they',
            'will', 'would', 'there', 'their', 'what', 'about', 'which',
            'when', 'make', 'like', 'time', 'very', 'your', 'how',
        }
        reference_words -= stopwords
        answer_words -= stopwords

        if not reference_words:
            return {"score": 5.0, "similarity": 0.5}

        overlap = reference_words & answer_words
        ratio = len(overlap) / len(reference_words)

        score = min(10.0, ratio * 15.0)
        return {"score": max(0.0, score), "similarity": ratio}

    # ══════════════════════════════════════════════════════════════════════════
    # STRUCTURE SCORING (Improvement #3)
    # ══════════════════════════════════════════════════════════════════════════

    def _score_structure(self, answer: str, question: Question) -> Dict:
        """
        Score the structural quality of the answer.
        Rewards: STAR method, numbered steps, pros/cons, comparisons, examples.
        """
        answer_lower = answer.lower()
        word_count = len(answer.split())

        # Very short answers can't have good structure
        if word_count < 15:
            return {"score": 3.0, "patterns_found": [], "bonus_applied": 0}

        patterns_found = []
        total_bonus = 0.0

        for pattern_name, config in STRUCTURE_PATTERNS.items():
            matched = False

            # Check regex patterns
            for pattern in config["patterns"]:
                if re.search(pattern, answer_lower, re.DOTALL | re.IGNORECASE):
                    matched = True
                    break

            # Check keyword groups (for STAR method)
            if not matched and "keywords" in config:
                groups_matched = 0
                for group in config["keywords"]:
                    if any(kw in answer_lower for kw in group):
                        groups_matched += 1
                if groups_matched >= config.get("min_keyword_groups", 3):
                    matched = True

            # Check counter patterns (for numbered steps, multiple examples)
            if not matched and "counter_pattern" in config:
                count = len(re.findall(config["counter_pattern"], answer, re.MULTILINE))
                if count >= config.get("min_count", 3):
                    matched = True

            if matched:
                patterns_found.append(pattern_name)
                total_bonus += config["bonus"]

        # Calculate base structure score
        # Base: check for paragraphs, sentences, logical flow
        sentences = re.split(r'[.!?]+', answer)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        num_sentences = len(sentences)

        # Base structure score from sentence count and variety
        if num_sentences >= 5:
            base_score = 6.0
        elif num_sentences >= 3:
            base_score = 5.0
        elif num_sentences >= 2:
            base_score = 4.0
        else:
            base_score = 3.0

        # Add bonuses for detected patterns (capped)
        final_score = min(10.0, base_score + total_bonus)

        # Behavioral questions: reward STAR method more
        if question.question_type == "behavioral" and "star_method" in patterns_found:
            final_score = min(10.0, final_score + 1.0)

        return {
            "score": final_score,
            "patterns_found": patterns_found,
            "bonus_applied": round(total_bonus, 1),
        }

    # ══════════════════════════════════════════════════════════════════════════
    # COMMUNICATION QUALITY (Improvement #5)
    # ══════════════════════════════════════════════════════════════════════════

    def _score_communication(self, answer: str) -> Dict:
        """
        Score communication quality:
        - Clarity (sentence length variance, not too long/short)
        - Coherence (transition words, logical connectors)
        - Professional language (technical vocabulary, no excessive filler)
        - Sentence variety (not all same structure)
        """
        answer_lower = answer.lower()
        word_count = len(answer.split())

        if word_count < 5:
            return {"score": 2.0, "details": {"too_short": True}}

        scores = {}

        # ─── 1. Filler word penalty ───────────────────────────────────
        filler_count = 0
        for pattern in FILLER_PATTERNS:
            filler_count += len(re.findall(pattern, answer_lower))

        filler_ratio = filler_count / max(word_count, 1)
        if filler_ratio > 0.05:
            scores["filler"] = 3.0
        elif filler_ratio > 0.02:
            scores["filler"] = 6.0
        elif filler_count > 0:
            scores["filler"] = 8.0
        else:
            scores["filler"] = 10.0

        # ─── 2. Hedging penalty ───────────────────────────────────────
        hedging_count = 0
        for pattern in HEDGING_PATTERNS:
            hedging_count += len(re.findall(pattern, answer_lower))

        hedging_ratio = hedging_count / max(word_count, 1)
        if hedging_ratio > 0.03:
            scores["hedging"] = 4.0
        elif hedging_count > 2:
            scores["hedging"] = 6.0
        elif hedging_count > 0:
            scores["hedging"] = 8.0
        else:
            scores["hedging"] = 9.0

        # ─── 3. Professional vocabulary ───────────────────────────────
        professional_count = 0
        for pattern in PROFESSIONAL_LANGUAGE:
            professional_count += len(re.findall(pattern, answer_lower))

        prof_ratio = professional_count / max(word_count / 20, 1)  # Per 20 words
        if prof_ratio >= 3:
            scores["professional"] = 10.0
        elif prof_ratio >= 2:
            scores["professional"] = 8.0
        elif prof_ratio >= 1:
            scores["professional"] = 6.0
        else:
            scores["professional"] = 4.0

        # ─── 4. Transition/coherence ──────────────────────────────────
        transition_count = 0
        for pattern in TRANSITION_PHRASES:
            transition_count += len(re.findall(pattern, answer_lower))

        if transition_count >= 4:
            scores["coherence"] = 10.0
        elif transition_count >= 2:
            scores["coherence"] = 7.0
        elif transition_count >= 1:
            scores["coherence"] = 5.0
        else:
            scores["coherence"] = 3.0

        # ─── 5. Sentence variety ──────────────────────────────────────
        sentences = re.split(r'[.!?]+', answer)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

        if len(sentences) >= 2:
            lengths = [len(s.split()) for s in sentences]
            avg_len = sum(lengths) / len(lengths)
            variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
            std_dev = math.sqrt(variance)

            # Good variety: std_dev between 3 and 15
            if 3 <= std_dev <= 15:
                scores["variety"] = 9.0
            elif std_dev > 15:
                scores["variety"] = 6.0  # Too erratic
            elif std_dev >= 1:
                scores["variety"] = 7.0
            else:
                scores["variety"] = 5.0  # All same length = robotic
        else:
            scores["variety"] = 5.0

        # Weighted combination
        weights = {
            "filler": 0.25,
            "hedging": 0.15,
            "professional": 0.25,
            "coherence": 0.20,
            "variety": 0.15,
        }

        final_score = sum(scores[k] * weights[k] for k in weights)

        return {
            "score": min(10.0, max(0.0, final_score)),
            "details": scores,
        }

    # ══════════════════════════════════════════════════════════════════════════
    # HELPER METHODS (shared with v1 for backward compatibility)
    # ══════════════════════════════════════════════════════════════════════════

    def _keyword_present(self, text: str, keyword: str) -> bool:
        """Check if a keyword (or its variations) is present in text."""
        if keyword in text:
            return True

        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text):
            return True

        variations = self._get_keyword_variations(keyword)
        for variation in variations:
            if variation in text:
                return True

        return False

    def _get_keyword_variations(self, keyword: str) -> List[str]:
        """Generate common variations of a keyword."""
        variations = []

        # Hyphenation variations
        if '-' in keyword:
            variations.append(keyword.replace('-', ' '))
            variations.append(keyword.replace('-', ''))
        elif ' ' in keyword:
            variations.append(keyword.replace(' ', '-'))
            variations.append(keyword.replace(' ', ''))

        # Common abbreviations (v1 compatibility)
        abbrevs = {
            "object-oriented": ["oop", "oo"],
            "database": ["db"],
            "application": ["app"],
            "configuration": ["config"],
            "repository": ["repo"],
            "continuous integration": ["ci"],
            "continuous deployment": ["cd"],
            "function": ["func", "fn"],
            "implementation": ["impl"],
            "authentication": ["auth", "authn"],
            "authorization": ["authz"],
            "infrastructure": ["infra"],
        }

        if keyword in abbrevs:
            variations.extend(abbrevs[keyword])

        # Plural/singular
        if keyword.endswith('s') and len(keyword) > 3:
            variations.append(keyword[:-1])
        elif not keyword.endswith('s'):
            variations.append(keyword + 's')

        # -ing / -tion / -ment forms
        if keyword.endswith('e'):
            variations.append(keyword[:-1] + 'ing')
        elif not keyword.endswith('ing'):
            variations.append(keyword + 'ing')

        return variations

    def _keyword_ratio_to_score(self, ratio: float) -> float:
        """Convert keyword match ratio to a score using a curve."""
        if ratio <= 0:
            return 0.0
        elif ratio >= 1.0:
            return 10.0
        else:
            return 10.0 * (1 - (1 - ratio) ** 1.5)

    def _score_length(self, answer: str, difficulty: str) -> Dict:
        """Score based on answer length appropriateness."""
        words = answer.split()
        word_count = len(words)

        if difficulty == "easy":
            min_words = MIN_WORDS_EASY
            ideal_words = IDEAL_WORDS_EASY
        elif difficulty == "medium":
            min_words = MIN_WORDS_MEDIUM
            ideal_words = IDEAL_WORDS_MEDIUM
        else:
            min_words = MIN_WORDS_HARD
            ideal_words = IDEAL_WORDS_HARD

        if word_count < min_words // 2:
            score = max(1.0, (word_count / min_words) * 4.0)
        elif word_count < min_words:
            score = 3.0 + (word_count - min_words // 2) / (min_words // 2) * 3.0
        elif word_count <= ideal_words:
            progress = (word_count - min_words) / max(1, ideal_words - min_words)
            score = 6.0 + progress * 4.0
        elif word_count <= MAX_WORDS_PENALTY:
            score = 9.0
        else:
            excess_ratio = (word_count - MAX_WORDS_PENALTY) / MAX_WORDS_PENALTY
            score = max(6.0, 9.0 - excess_ratio * 3.0)

        return {"score": min(10.0, score), "word_count": word_count}

    def _calculate_quality_modifier(self, answer: str) -> float:
        """Calculate bonus/penalty based on answer quality indicators (v1 compat)."""
        modifier = 0.0
        answer_lower = answer.lower()

        filler_count = 0
        for pattern in FILLER_PATTERNS:
            filler_count += len(re.findall(pattern, answer_lower))

        if filler_count > 5:
            modifier -= 0.8
        elif filler_count > 2:
            modifier -= 0.4

        quality_count = 0
        for pattern in QUALITY_INDICATORS:
            quality_count += len(re.findall(pattern, answer_lower))

        if quality_count >= 4:
            modifier += 0.8
        elif quality_count >= 2:
            modifier += 0.4

        if re.search(r'(?:^|\n)\s*(?:\d+[.):]|\-|\*|•)', answer):
            modifier += 0.2

        return modifier

    def _calculate_confidence(
        self, keyword_result: Dict, concept_result: Dict,
        length_result: Dict, answer: str
    ) -> float:
        """Calculate confidence in the evaluation (0-1)."""
        confidence = 0.5

        total_keywords = len(keyword_result["found"]) + len(keyword_result["missed"])
        if total_keywords >= 8:
            confidence += 0.15
        elif total_keywords >= 5:
            confidence += 0.1

        # Concept matches increase confidence
        if concept_result.get("related_found"):
            confidence += 0.1

        word_count = length_result.get("word_count", 0)
        if word_count > 80:
            confidence += 0.2
        elif word_count > 50:
            confidence += 0.15
        elif word_count > 20:
            confidence += 0.1

        if word_count < 10:
            confidence = 0.3

        return min(1.0, confidence)

    # ══════════════════════════════════════════════════════════════════════════
    # STRENGTHS & IMPROVEMENTS GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _identify_strengths(
        self,
        keyword_result: Dict,
        concept_result: Dict,
        length_result: Dict,
        relevance_result: Dict,
        structure_result: Dict,
        communication_result: Dict,
        answer: str,
    ) -> List[str]:
        """Identify strengths in the answer."""
        strengths = []
        answer_lower = answer.lower()

        # Keywords & Concepts
        found = keyword_result["found"]
        synonym_matches = keyword_result.get("synonym_matches", [])
        if len(found) >= 5:
            strengths.append(
                f"Excellent coverage of key concepts ({len(found)} relevant terms used)"
            )
        elif len(found) >= 3:
            strengths.append(
                f"Good mention of important concepts: {', '.join(found[:4])}"
            )

        if synonym_matches:
            strengths.append(
                f"Demonstrated understanding through varied terminology "
                f"(e.g., {', '.join(synonym_matches[:2])})"
            )

        # Related concepts (partial credit)
        related = concept_result.get("related_found", [])
        if len(related) >= 2:
            strengths.append(
                f"Good awareness of related concepts: {', '.join(related[:3])}"
            )

        # Length
        if length_result["score"] >= 8.0:
            strengths.append("Well-detailed response with appropriate depth")

        # Relevance
        if relevance_result["score"] >= 7.0:
            strengths.append("Highly relevant and on-topic response")

        # Structure
        patterns_found = structure_result.get("patterns_found", [])
        if "star_method" in patterns_found:
            strengths.append("Well-structured using STAR method (Situation-Task-Action-Result)")
        elif "numbered_steps" in patterns_found:
            strengths.append("Clear step-by-step structure aids comprehension")
        elif "pros_cons" in patterns_found:
            strengths.append("Balanced analysis with pros/cons demonstrates critical thinking")
        elif "comparison" in patterns_found:
            strengths.append("Effective comparative analysis")

        # Communication
        comm_details = communication_result.get("details", {})
        if comm_details.get("professional", 0) >= 8:
            strengths.append("Professional and technically precise language")
        if comm_details.get("coherence", 0) >= 8:
            strengths.append("Excellent logical flow with clear transitions")

        # Example usage
        if re.search(r'\b(for example|such as|e\.g\.)', answer_lower):
            strengths.append("Good use of examples to illustrate points")
        if re.search(r'\b(trade-off|pros? and cons?|advantage|disadvantage)', answer_lower):
            strengths.append("Shows awareness of trade-offs")
        if re.search(r'\b(in practice|production|real-world|at scale)', answer_lower):
            strengths.append("Demonstrates practical/production experience")

        return strengths[:6]  # Limit to top 6

    def _identify_improvements(
        self,
        keyword_result: Dict,
        concept_result: Dict,
        length_result: Dict,
        relevance_result: Dict,
        structure_result: Dict,
        communication_result: Dict,
        answer: str,
        question: Question,
    ) -> List[str]:
        """Identify areas for improvement."""
        improvements = []
        answer_lower = answer.lower()
        missed = keyword_result["missed"]
        word_count = length_result.get("word_count", 0)

        # Missed keywords
        if len(missed) >= 5:
            improvements.append(
                f"Consider discussing: {', '.join(missed[:4])}"
            )
        elif len(missed) >= 2:
            improvements.append(
                f"Could strengthen by mentioning: {', '.join(missed[:3])}"
            )

        # Length issues
        if word_count < 20:
            improvements.append(
                "Answer is very brief. Try to elaborate with examples and reasoning."
            )
        elif word_count < 40 and question.difficulty in ("medium", "hard"):
            improvements.append(
                "Consider adding more detail, examples, or trade-off analysis."
            )
        elif word_count > MAX_WORDS_PENALTY:
            improvements.append(
                "Answer is quite lengthy. Consider being more concise and focused."
            )

        # Relevance
        if relevance_result["score"] < 4.0:
            improvements.append(
                "The response could be more focused on the specific question asked."
            )

        # Structure improvements
        patterns_found = structure_result.get("patterns_found", [])
        if not patterns_found and word_count > 80:
            improvements.append(
                "Consider structuring your answer with numbered points, "
                "examples, or a clear framework (e.g., STAR for behavioral questions)."
            )
        if question.question_type == "behavioral" and "star_method" not in patterns_found:
            improvements.append(
                "For behavioral questions, use the STAR method: "
                "Situation → Task → Action → Result."
            )

        # Communication improvements
        comm_details = communication_result.get("details", {})
        if comm_details.get("filler", 10) < 5:
            improvements.append(
                "Reduce filler words (um, basically, like) for more impactful delivery."
            )
        if comm_details.get("hedging", 10) < 5:
            improvements.append(
                "Project more confidence — avoid excessive hedging "
                "(maybe, I think, I'm not sure)."
            )
        if comm_details.get("coherence", 10) < 5:
            improvements.append(
                "Use transition phrases (however, therefore, additionally) "
                "to connect ideas more smoothly."
            )
        if comm_details.get("professional", 10) < 5:
            improvements.append(
                "Incorporate more technical vocabulary relevant to the topic."
            )

        # Examples
        if not re.search(r'\b(for example|such as|e\.g\.|instance)', answer_lower):
            if question.difficulty in ("medium", "hard"):
                improvements.append(
                    "Adding specific examples would strengthen the answer."
                )

        return improvements[:6]  # Limit to top 6

    def _normalize_text(self, text: str) -> str:
        """Normalize text for evaluation."""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text


# ══════════════════════════════════════════════════════════════════════════════
# BACKWARD-COMPATIBLE PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════
# Matches the exact signature used in interview_agent.py:
#
#   evaluation = evaluate_answer(
#       question_text=question_text,
#       answer_text=user_message,
#       expected_keywords=expected_keywords,
#   )
#
# Returns: dict with score, strengths, gaps, model_answer_hint, acknowledgment
# ══════════════════════════════════════════════════════════════════════════════

_evaluator_instance: Optional[AnswerEvaluatorV2] = None


def evaluate_answer(
    question_text: str,
    answer_text: str,
    expected_keywords: list = None,
    difficulty: str = "medium",
) -> dict:
    """
    Evaluate a candidate's answer and return scoring details.

    This is the main entry point used by interview_agent.py.
    BACKWARD COMPATIBLE with v1 signature and return format.

    Args:
        question_text: The interview question that was asked
        answer_text: The candidate's response
        expected_keywords: List of keywords a good answer should mention
        difficulty: easy/medium/hard

    Returns:
        dict with: score (0-10), strengths (list), gaps (list),
        model_answer_hint (str), acknowledgment (str),
        keywords_found (list), keywords_missed (list)
    """
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = AnswerEvaluatorV2()

    # Create a Question-like object for the evaluator
    question_obj = Question(
        id="eval_q",
        text=question_text,
        topic="",
        difficulty=difficulty,
        category="technical",
        question_type="technical",
        expected_keywords=expected_keywords or [],
        model_answer_hint="",
    )

    result = _evaluator_instance.evaluate(
        answer=answer_text,
        question=question_obj,
    )

    # Convert EvaluationResult to dict with expected keys (v1 format)
    return {
        "score": int(round(result.score)),
        "strengths": result.strengths or [],
        "gaps": result.improvements or [],
        "model_answer_hint": result.model_answer_hint or "",
        "acknowledgment": _generate_acknowledgment(int(round(result.score))),
        "keywords_found": result.keywords_found or [],
        "keywords_missed": result.keywords_missed or [],
        # v2 additions (non-breaking — extra keys)
        "concept_score": result.concept_score,
        "structure_score": result.structure_score,
        "communication_score": result.communication_score,
    }


def _generate_acknowledgment(score: int) -> str:
    """Generate a brief acknowledgment based on score."""
    if score >= 9:
        return "✅ **Outstanding answer!** You demonstrated deep expertise and clear communication."
    elif score >= 7:
        return "✅ **Excellent answer!** You demonstrated strong understanding."
    elif score >= 6:
        return "👍 **Good answer.** You covered the key points well."
    elif score >= 4:
        return "💡 **Decent attempt.** There's room to deepen your explanation."
    elif score >= 2:
        return "⚠️ **Needs improvement.** Try to be more specific with examples and key concepts."
    else:
        return "⚠️ **Very brief or off-topic.** Review the topic and try a more detailed response."


# ══════════════════════════════════════════════════════════════════════════════
# LEGACY COMPATIBILITY: AnswerEvaluator alias
# ══════════════════════════════════════════════════════════════════════════════
# If any code imports `AnswerEvaluator` from this module, it gets the v2 class.
AnswerEvaluator = AnswerEvaluatorV2
