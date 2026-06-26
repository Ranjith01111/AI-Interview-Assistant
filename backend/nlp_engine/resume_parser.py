"""
Resume Parser — Extracts skills, experience, projects from PDF text using regex and keyword matching.

No spaCy, no NLP models. Pure Python regex + curated keyword lists.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set


@dataclass
class ParsedResume:
    """Structured resume data extracted from raw text."""
    skills: List[str] = field(default_factory=list)
    experience_years: float = 0.0
    job_titles: List[str] = field(default_factory=list)
    projects: List[Dict[str, str]] = field(default_factory=list)
    education: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    summary: str = ""
    raw_text: str = ""
    skill_categories: Dict[str, List[str]] = field(default_factory=dict)


# Comprehensive skill keyword database organized by category
SKILL_KEYWORDS: Dict[str, List[str]] = {
    "python": [
        "python", "django", "flask", "fastapi", "celery", "asyncio",
        "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
        "pytest", "unittest", "poetry", "pip", "virtualenv", "conda",
        "pydantic", "sqlalchemy", "alembic", "uvicorn", "gunicorn",
        "tornado", "aiohttp", "requests", "beautifulsoup", "scrapy",
        "tkinter", "pyqt", "kivy", "pygame", "pillow", "opencv-python",
    ],
    "javascript": [
        "javascript", "typescript", "node.js", "nodejs", "express",
        "express.js", "npm", "yarn", "webpack", "babel", "eslint",
        "jest", "mocha", "chai", "jasmine", "karma", "cypress",
        "jquery", "lodash", "axios", "fetch api", "websocket",
        "socket.io", "graphql", "apollo", "next.js", "nextjs",
        "nuxt.js", "nuxtjs", "deno", "bun", "esbuild", "vite",
        "rollup", "parcel", "pnpm", "es6", "ecmascript",
    ],
    "react": [
        "react", "react.js", "reactjs", "redux", "react redux",
        "react hooks", "usestate", "useeffect", "usecontext",
        "react router", "material-ui", "mui", "chakra ui",
        "styled-components", "emotion", "tailwind", "ant design",
        "react query", "tanstack query", "zustand", "recoil",
        "mobx", "formik", "react hook form", "storybook",
        "react native", "gatsby", "remix",
    ],
    "sql": [
        "sql", "mysql", "postgresql", "postgres", "sqlite", "oracle",
        "sql server", "mssql", "t-sql", "pl/sql", "mariadb",
        "stored procedures", "triggers", "views", "indexes",
        "normalization", "denormalization", "query optimization",
        "joins", "subqueries", "cte", "window functions",
        "database design", "er diagrams", "acid",
    ],
    "nosql": [
        "nosql", "mongodb", "cassandra", "dynamodb", "redis",
        "elasticsearch", "couchdb", "neo4j", "firebase",
        "firestore", "memcached", "couchbase", "hbase",
        "influxdb", "timescaledb", "arangodb",
    ],
    "aws": [
        "aws", "amazon web services", "ec2", "s3", "lambda",
        "dynamodb", "rds", "cloudfront", "route53", "iam",
        "vpc", "ecs", "eks", "fargate", "cloudwatch",
        "cloudformation", "terraform", "sqs", "sns", "kinesis",
        "api gateway", "cognito", "amplify", "elastic beanstalk",
        "sagemaker", "redshift", "athena", "glue", "step functions",
        "eventbridge", "aurora", "elasticache",
    ],
    "docker": [
        "docker", "dockerfile", "docker-compose", "docker compose",
        "kubernetes", "k8s", "helm", "container", "containerization",
        "microservices", "docker swarm", "podman", "containerd",
        "cri-o", "istio", "envoy", "service mesh",
    ],
    "machine_learning": [
        "machine learning", "deep learning", "neural network",
        "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
        "nlp", "natural language processing", "computer vision",
        "random forest", "decision tree", "svm", "support vector",
        "logistic regression", "linear regression", "clustering",
        "k-means", "knn", "gradient boosting", "xgboost", "lightgbm",
        "catboost", "cnn", "rnn", "lstm", "transformer", "bert",
        "gpt", "gan", "autoencoder", "reinforcement learning",
        "feature engineering", "hyperparameter tuning", "cross-validation",
        "overfitting", "underfitting", "regularization",
        "data preprocessing", "model evaluation", "mlops",
        "mlflow", "wandb", "huggingface", "spacy",
    ],
    "data_science": [
        "data science", "data analysis", "data visualization",
        "statistics", "probability", "hypothesis testing",
        "a/b testing", "etl", "data pipeline", "data warehouse",
        "business intelligence", "tableau", "power bi", "looker",
        "apache spark", "pyspark", "hadoop", "hive", "airflow",
        "dbt", "snowflake", "bigquery", "databricks",
    ],
    "system_design": [
        "system design", "distributed systems", "microservices",
        "load balancing", "caching", "cdn", "message queue",
        "event-driven", "rest api", "grpc", "graphql",
        "database sharding", "replication", "cap theorem",
        "scalability", "high availability", "fault tolerance",
        "circuit breaker", "rate limiting", "api gateway",
        "service discovery", "saga pattern", "cqrs",
        "event sourcing", "domain-driven design", "ddd",
    ],
    "devops": [
        "devops", "ci/cd", "jenkins", "github actions",
        "gitlab ci", "circleci", "travis ci", "ansible",
        "puppet", "chef", "terraform", "infrastructure as code",
        "monitoring", "prometheus", "grafana", "datadog",
        "new relic", "elk stack", "logstash", "kibana",
        "nginx", "apache", "linux", "bash", "shell scripting",
    ],
    "git": [
        "git", "github", "gitlab", "bitbucket", "version control",
        "branching", "merging", "pull request", "code review",
        "git flow", "trunk-based development", "rebase",
        "cherry-pick", "git hooks", "submodules",
    ],
    "testing": [
        "testing", "unit testing", "integration testing",
        "end-to-end testing", "e2e", "tdd", "bdd",
        "test automation", "selenium", "playwright", "puppeteer",
        "cypress", "jest", "pytest", "junit", "testng",
        "mocking", "stubbing", "code coverage", "load testing",
        "performance testing", "jmeter", "k6", "locust",
    ],
    "security": [
        "security", "authentication", "authorization", "oauth",
        "oauth2", "jwt", "ssl", "tls", "https", "encryption",
        "hashing", "bcrypt", "cors", "csrf", "xss",
        "sql injection", "owasp", "penetration testing",
        "vulnerability assessment", "firewall", "waf",
        "security audit", "compliance", "gdpr", "hipaa",
        "soc2", "rbac", "mfa", "two-factor",
    ],
    "api_design": [
        "rest", "restful", "api design", "openapi", "swagger",
        "graphql", "grpc", "protobuf", "websocket",
        "api versioning", "pagination", "rate limiting",
        "api documentation", "postman", "insomnia",
        "http methods", "status codes", "hateoas",
    ],
    "data_structures": [
        "data structures", "algorithms", "array", "linked list",
        "stack", "queue", "tree", "binary tree", "bst",
        "heap", "hash table", "hash map", "graph",
        "sorting", "searching", "dynamic programming",
        "recursion", "big o", "time complexity", "space complexity",
        "dfs", "bfs", "dijkstra", "greedy", "backtracking",
        "trie", "segment tree", "binary search",
    ],
    "mobile": [
        "react native", "flutter", "swift", "kotlin",
        "ios", "android", "mobile development", "xamarin",
        "ionic", "capacitor", "expo", "swiftui",
        "jetpack compose", "objective-c", "dart",
    ],
    "cloud_general": [
        "cloud computing", "azure", "gcp", "google cloud",
        "heroku", "digital ocean", "vercel", "netlify",
        "serverless", "paas", "iaas", "saas", "multi-cloud",
    ],
    "java": [
        "java", "spring", "spring boot", "hibernate", "maven",
        "gradle", "jpa", "jdbc", "servlets", "jsp",
        "microservices", "java ee", "jakarta ee", "quarkus",
        "micronaut", "lombok", "jvm", "multithreading",
    ],
    "csharp": [
        "c#", "csharp", ".net", "asp.net", "entity framework",
        "linq", "blazor", "wpf", "winforms", "xamarin",
        "unity", ".net core", "nuget", "azure devops",
    ],
    "go": [
        "go", "golang", "goroutine", "channels", "gin",
        "echo", "fiber", "grpc-go", "cobra", "viper",
    ],
    "rust": [
        "rust", "cargo", "tokio", "actix", "wasm",
        "webassembly", "ownership", "borrowing", "lifetimes",
    ],
}

# Job title patterns
JOB_TITLE_PATTERNS = [
    r"(?:senior|sr\.?|junior|jr\.?|lead|principal|staff|chief|head of|vp of|director of)?\s*"
    r"(?:software|web|frontend|front-end|backend|back-end|full[- ]?stack|mobile|cloud|devops|data|ml|ai|platform|infrastructure)?\s*"
    r"(?:engineer|developer|architect|scientist|analyst|manager|consultant|specialist|administrator|designer)",
    r"(?:cto|cio|vp engineering|tech lead|team lead|engineering manager)",
    r"(?:sre|site reliability engineer)",
    r"(?:product manager|project manager|scrum master|agile coach)",
    r"(?:qa engineer|quality assurance|test engineer|sdet)",
    r"(?:database administrator|dba|system administrator|sysadmin)",
]

# Education patterns
EDUCATION_KEYWORDS = [
    r"(?:bachelor|master|phd|doctorate|associate|diploma|certificate)\s*(?:of|in|'s)?\s*"
    r"(?:science|arts|engineering|technology|computer science|information technology|mathematics|statistics|physics|business)?",
    r"b\.?s\.?\s*(?:in\s+)?(?:computer science|cs|it|engineering|mathematics)",
    r"m\.?s\.?\s*(?:in\s+)?(?:computer science|cs|it|engineering|data science|ai|ml)",
    r"b\.?tech|m\.?tech|b\.?e\.?|m\.?e\.?|mba|bba|bca|mca",
    r"ph\.?d\.?\s*(?:in\s+)?(?:computer science|cs|engineering|mathematics|ai|ml)",
]

# Certification patterns
CERTIFICATION_KEYWORDS = [
    r"aws\s+(?:certified|solutions architect|developer|sysops|devops|cloud practitioner)",
    r"(?:azure|microsoft)\s+(?:certified|fundamentals|administrator|developer|architect)",
    r"google\s+cloud\s+(?:certified|professional|associate)",
    r"(?:pmp|prince2|itil|cissp|cism|cisa|comptia|ccna|ccnp)",
    r"(?:certified\s+)?(?:kubernetes|ckad|cka|cks)",
    r"(?:certified\s+)?scrum\s+(?:master|product owner|developer)",
    r"(?:oracle|java)\s+(?:certified|professional|associate)",
    r"terraform\s+(?:certified|associate)",
]


class ResumeParser:
    """Parses resume text and extracts structured data using regex and keyword matching."""

    def __init__(self):
        self._skill_patterns = self._compile_skill_patterns()
        self._title_patterns = [re.compile(p, re.IGNORECASE) for p in JOB_TITLE_PATTERNS]
        self._education_patterns = [re.compile(p, re.IGNORECASE) for p in EDUCATION_KEYWORDS]
        self._certification_patterns = [re.compile(p, re.IGNORECASE) for p in CERTIFICATION_KEYWORDS]

    def _compile_skill_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Pre-compile regex patterns for all skills."""
        compiled = {}
        for category, keywords in SKILL_KEYWORDS.items():
            patterns = []
            for kw in keywords:
                # Escape special regex chars, create word-boundary pattern
                escaped = re.escape(kw)
                # Allow for common variations (dots, hyphens)
                pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
                patterns.append((kw, pattern))
            compiled[category] = patterns
        return compiled

    def parse(self, text: str) -> ParsedResume:
        """Parse resume text and return structured data."""
        result = ParsedResume(raw_text=text)

        # Normalize text
        normalized = self._normalize_text(text)

        # Extract components
        result.skills = self._extract_skills(normalized)
        result.skill_categories = self._categorize_skills(normalized)
        result.experience_years = self._extract_experience_years(normalized)
        result.job_titles = self._extract_job_titles(normalized)
        result.projects = self._extract_projects(normalized)
        result.education = self._extract_education(normalized)
        result.certifications = self._extract_certifications(normalized)
        result.summary = self._extract_summary(normalized)

        return result

    def _normalize_text(self, text: str) -> str:
        """Normalize text: fix encoding issues, standardize whitespace."""
        # Replace common PDF artifacts
        text = re.sub(r'\x00', '', text)
        text = re.sub(r'[\u2018\u2019]', "'", text)
        text = re.sub(r'[\u201c\u201d]', '"', text)
        text = re.sub(r'[\u2013\u2014]', '-', text)
        text = re.sub(r'\u2022', '•', text)
        # Normalize whitespace but preserve newlines
        text = re.sub(r'[^\S\n]+', ' ', text)
        # Remove excessive newlines
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        return text.strip()

    def _extract_skills(self, text: str) -> List[str]:
        """Extract all detected skills as a flat list."""
        found_skills: Set[str] = set()
        text_lower = text.lower()

        for category, patterns in self._skill_patterns.items():
            for skill_name, pattern in patterns:
                if pattern.search(text_lower):
                    found_skills.add(skill_name)

        return sorted(list(found_skills))

    def _categorize_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract skills organized by category."""
        categorized: Dict[str, List[str]] = {}
        text_lower = text.lower()

        for category, patterns in self._skill_patterns.items():
            category_skills = []
            for skill_name, pattern in patterns:
                if pattern.search(text_lower):
                    category_skills.append(skill_name)
            if category_skills:
                categorized[category] = category_skills

        return categorized

    def _extract_experience_years(self, text: str) -> float:
        """
        Extract total years of experience from resume text.
        Works with ANY resume format — doesn't expect standard sections.
        
        Logic:
        1. If resume clearly indicates fresher/student → 0
        2. If resume explicitly says "X years experience" → use that
        3. If resume has work-related date ranges (NOT in education/projects) → calculate
        4. Otherwise → 0 (don't guess)
        """
        text_lower = text.lower()

        # ── Step 1: Fresher/Student detection (broad matching)
        fresher_phrases = [
            'entry-level', 'entry level', 'fresher', 'freshman',
            'seeking my first', 'looking for my first',
            'recent graduate', 'no experience', 'no work experience',
            'aspiring developer', 'aspiring engineer', 'aspiring scientist',
        ]
        for phrase in fresher_phrases:
            if phrase in text_lower:
                return 0.0

        # Check if the person is still a student (strong indicator = fresher)
        is_student = bool(re.search(r'\bstudent\b', text_lower))
        has_no_work_section = not bool(re.search(
            r'(?:work\s*experience|professional\s*experience|employment\s*history|work\s*history|career\s*history)',
            text_lower
        ))
        seeking_role = bool(re.search(r'seeking\s+(?:a|an)?\s*\w+\s*(?:role|position|opportunity|job)', text_lower))
        
        if is_student and (has_no_work_section or seeking_role):
            return 0.0

        # ── Step 2: Explicit mention like "5 years of experience"
        patterns = [
            r'(\d+\.?\d*)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)',
            r'(?:experience|exp)\s*(?:of\s+)?(\d+\.?\d*)\+?\s*(?:years?|yrs?)',
            r'(\d+\.?\d*)\+?\s*(?:years?|yrs?)\s*(?:in\s+)?(?:software|web|development|engineering|programming|it|tech)',
            r'(?:over|more than|approximately|about|nearly)\s*(\d+\.?\d*)\s*(?:years?|yrs?)',
        ]

        max_years = 0.0
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    years = float(match)
                    if 0 < years <= 50:
                        max_years = max(max_years, years)
                except (ValueError, IndexError):
                    continue

        if max_years > 0:
            return max_years

        # ── Step 3: Date range calculation — ONLY if work section exists
        # If there's no explicit work/experience section, don't guess from random dates
        if has_no_work_section:
            return 0.0

        # Extract only from work experience section
        work_match = re.search(
            r'(?:work\s*experience|professional\s*experience|employment|career\s*history|work\s*history)[\s:]*(.+?)(?=\n\s*(?:education|project|certif|skill|achievement|hobby|interest|technical)|$)',
            text_lower,
            re.DOTALL
        )
        if work_match:
            import datetime
            work_text = work_match.group(1)
            date_ranges = re.findall(
                r'(20\d{2}|19\d{2})\s*[-–—to]+\s*(20\d{2}|19\d{2}|present|current|now|ongoing)',
                work_text
            )
            if date_ranges:
                current_year = datetime.datetime.now().year
                total_years = 0.0
                for start, end in date_ranges:
                    start_year = int(start)
                    end_year = current_year if end in ('present', 'current', 'now', 'ongoing') else int(end)
                    duration = end_year - start_year
                    if 0 < duration <= 30:
                        total_years += duration
                return min(total_years, 40.0)

        return 0.0

    def _extract_job_titles(self, text: str) -> List[str]:
        """Extract job titles from resume."""
        titles = []
        for pattern in self._title_patterns:
            matches = pattern.findall(text)
            for match in matches:
                cleaned = match.strip()
                if cleaned and len(cleaned) > 3:
                    titles.append(cleaned)

        # Deduplicate while preserving order
        seen = set()
        unique_titles = []
        for title in titles:
            title_lower = title.lower()
            if title_lower not in seen:
                seen.add(title_lower)
                unique_titles.append(title)

        return unique_titles[:10]  # Limit to 10 most relevant

    def _extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract project descriptions from resume."""
        projects = []

        # Look for project sections
        project_section = re.search(
            r'(?:projects?|portfolio|key\s+projects?|notable\s+projects?)\s*[:\n](.+?)(?=\n\s*(?:education|certif|skills|experience|work|employ|reference|hobbies|interest)|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )

        if project_section:
            section_text = project_section.group(1)
            # Split by bullet points or numbered items
            items = re.split(r'(?:\n\s*[•\-\*\d\.]+\s*|\n{2,})', section_text)
            for item in items:
                item = item.strip()
                if len(item) > 20:  # Minimum meaningful length
                    # Try to extract project name and description
                    name_match = re.match(r'^([^:\-\n]{5,60})[\s:\-–]+(.+)', item, re.DOTALL)
                    if name_match:
                        projects.append({
                            "name": name_match.group(1).strip(),
                            "description": name_match.group(2).strip()[:300]
                        })
                    else:
                        projects.append({
                            "name": item[:50].strip(),
                            "description": item[:300].strip()
                        })

        return projects[:10]

    def _extract_education(self, text: str) -> List[str]:
        """Extract education qualifications."""
        education = []
        for pattern in self._education_patterns:
            matches = pattern.findall(text)
            for match in matches:
                cleaned = match.strip()
                if cleaned and len(cleaned) > 2:
                    education.append(cleaned)

        # Deduplicate
        return list(dict.fromkeys(education))[:5]

    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications."""
        certifications = []
        for pattern in self._certification_patterns:
            matches = pattern.findall(text)
            for match in matches:
                cleaned = match.strip()
                if cleaned and len(cleaned) > 3:
                    certifications.append(cleaned)

        return list(dict.fromkeys(certifications))[:10]

    def _extract_summary(self, text: str) -> str:
        """Extract professional summary/objective section."""
        summary_match = re.search(
            r'(?:summary|objective|profile|about\s+me|professional\s+summary)\s*[:\n](.+?)(?=\n\s*(?:experience|skills|education|work|employ|technical|projects?)|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )
        if summary_match:
            summary = summary_match.group(1).strip()
            # Clean and truncate
            summary = re.sub(r'\s+', ' ', summary)
            return summary[:500]
        return ""

    def get_experience_level(self, years: float) -> str:
        """Classify experience level."""
        if years <= 2:
            return "junior"
        elif years <= 5:
            return "mid"
        elif years <= 10:
            return "senior"
        else:
            return "expert"

    def get_difficulty_for_experience(self, years: float) -> str:
        """Map experience years to appropriate question difficulty."""
        if years <= 2:
            return "easy"
        elif years <= 5:
            return "medium"
        else:
            return "hard"


# ── Convenience function (matches service import) ────────────────────────
_parser_instance = None

def parse_resume_structured(text: str) -> dict:
    """
    Parse resume text and return structured data as a dict.
    
    This is the main entry point used by resume_service.py.
    
    Returns:
        dict with keys: candidate_name, skills, skills_categorized,
        experience_years, experience_level, difficulty, job_titles,
        projects, education, certifications, summary
    """
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = ResumeParser()
    
    parsed = _parser_instance.parse(text)
    
    # Convert dataclass to dict
    result = {
        "candidate_name": _extract_candidate_name(text),
        "skills": parsed.skills,
        "skills_categorized": parsed.skill_categories,
        "experience_years": parsed.experience_years,
        "experience_level": _parser_instance.get_experience_level(parsed.experience_years),
        "difficulty": _parser_instance.get_difficulty_for_experience(parsed.experience_years),
        "job_titles": parsed.job_titles,
        "projects": parsed.projects,
        "education": parsed.education,
        "certifications": parsed.certifications,
        "summary": parsed.summary,
    }
    return result


def _extract_candidate_name(text: str) -> str:
    """
    Extract candidate name from resume text.
    Heuristic: first non-empty line that looks like a name (2-4 words, all alpha).
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines[:5]:  # check first 5 lines
        words = line.split()
        if 2 <= len(words) <= 4 and all(w.replace(".", "").replace(",", "").isalpha() for w in words):
            # Avoid lines that are section headers
            lower = line.lower()
            if lower not in ("career objective", "professional summary", "work experience", "key strengths"):
                return line.title()
    return "Candidate"
