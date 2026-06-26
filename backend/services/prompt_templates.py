"""
Prompt Templates — Specialized prompts for context-aware question generation.

Contains 4 question-generation strategies + an anti-generic guard.
Each template takes structured project JSON as input and produces
targeted interview questions that test real depth — never "What is Python?".

Categories:
  • PROJECT_DEEP_DIVE   — Questions about specific projects on their resume
  • CHALLENGE_SCENARIO  — Challenge/debugging scenarios from their tech stack
  • ARCHITECTURE_PROBE  — System design questions using their actual architecture
  • DEBUGGING_EXERCISE  — Realistic bug scenarios tied to their project context
"""

# ─────────────────────────────────────────────────────────────────────
# ANTI-GENERIC GUARD — Prepended to ALL prompts
# ─────────────────────────────────────────────────────────────────────
ANTI_GENERIC_GUARD = """
CRITICAL RULES — You MUST follow these strictly:
1. NEVER generate generic definition questions like:
   - "What is Python?"
   - "What is Java?"
   - "Explain OOP concepts"
   - "What is REST API?"
   - "Define machine learning"
   - "What are the features of <technology>?"
2. EVERY question MUST reference a SPECIFIC project, technology choice,
   or architecture decision from the candidate's resume.
3. Questions must test DEPTH of understanding, not surface-level knowledge.
4. Questions must be ones that ONLY this specific candidate can answer
   based on their unique project experience.
5. If you cannot generate a project-specific question, generate a
   scenario-based question using the candidate's actual tech stack.
"""


# ─────────────────────────────────────────────────────────────────────
# 1. PROJECT DEEP-DIVE QUESTIONS
# ─────────────────────────────────────────────────────────────────────
PROJECT_DEEP_DIVE_PROMPT = """
{anti_generic_guard}

You are a senior technical interviewer conducting a deep-dive into the candidate's
project experience. You have access to their structured project data below.

CANDIDATE PROFILE:
- Primary Skills: {primary_skills}
- Experience Level: {experience_level}
- Domain Expertise: {domain_expertise}

PROJECTS:
{projects_json}

ADDITIONAL RESUME CONTEXT:
{resume_context}

Generate exactly {num_questions} PROJECT-BASED interview questions.

Each question MUST:
- Reference a SPECIFIC project by name
- Ask about a specific technical decision, tradeoff, or implementation detail
- Test WHY they made certain choices, not WHAT they used
- Be appropriate for their experience level ({experience_level})

FORMAT — Return ONLY a valid JSON array:
[
  {{
    "question": "In your [Project Name] project, you chose [Technology X] for [purpose]. What tradeoffs did you consider vs [Alternative], and how did that choice affect [specific aspect]?",
    "topic": "the primary technology or concept being tested",
    "difficulty": "easy|medium|hard",
    "project_reference": "exact project name from the input"
  }}
]

Generate the questions now:
"""


# ─────────────────────────────────────────────────────────────────────
# 2. CHALLENGE / SCENARIO QUESTIONS
# ─────────────────────────────────────────────────────────────────────
CHALLENGE_SCENARIO_PROMPT = """
{anti_generic_guard}

You are a senior technical interviewer who specializes in testing problem-solving
ability. You will present REALISTIC challenge scenarios based on the candidate's
actual project experience.

CANDIDATE PROFILE:
- Primary Skills: {primary_skills}
- Experience Level: {experience_level}
- Domain Expertise: {domain_expertise}

PROJECTS (with challenges they faced):
{projects_json}

ADDITIONAL RESUME CONTEXT:
{resume_context}

Generate exactly {num_questions} CHALLENGE-BASED interview questions.

Each question MUST:
- Present a realistic scaling, performance, or reliability challenge
- Be grounded in their ACTUAL tech stack (not hypothetical stacks)
- Reference specific challenges or solutions from their projects
- Ask HOW they would handle a twist or escalation of their original challenge
- Test problem-solving approach, not textbook definitions

QUESTION STYLES TO USE:
- "Your [project] handles [X]. What happens when [realistic failure scenario]?"
- "You mentioned solving [challenge] with [solution]. Walk me through what breaks when [escalation]."
- "In [project], your [component] processes [volume]. How would you debug [specific symptom]?"

FORMAT — Return ONLY a valid JSON array:
[
  {{
    "question": "detailed scenario question referencing their specific project",
    "topic": "the primary concept being tested",
    "difficulty": "easy|medium|hard",
    "project_reference": "exact project name or 'cross-project'"
  }}
]

Generate the questions now:
"""


# ─────────────────────────────────────────────────────────────────────
# 3. ARCHITECTURE PROBE QUESTIONS
# ─────────────────────────────────────────────────────────────────────
ARCHITECTURE_PROBE_PROMPT = """
{anti_generic_guard}

You are a senior systems architect interviewing a candidate about their
architecture and design decisions. You will probe their understanding of
WHY their system is designed the way it is.

CANDIDATE PROFILE:
- Primary Skills: {primary_skills}
- Experience Level: {experience_level}
- Domain Expertise: {domain_expertise}

PROJECTS (with technology stacks and solutions):
{projects_json}

ADDITIONAL RESUME CONTEXT:
{resume_context}

Generate exactly {num_questions} ARCHITECTURE interview questions.

Each question MUST:
- Reference their actual system architecture (not a hypothetical one)
- Test understanding of component interactions, data flow, or system boundaries
- Ask about scalability, reliability, or maintainability of their designs
- Challenge them to evolve their current architecture for new requirements
- Be specific to THEIR stack — e.g., "your FastAPI + Redis + PostgreSQL setup"

QUESTION STYLES TO USE:
- "Your [project] uses [Architecture Pattern]. How would you redesign [component] if [new requirement]?"
- "Walk me through the data flow in your [project] from [entry point] to [storage]. Where are the bottlenecks?"
- "You chose [Database X] for [project]. How would the architecture change if you needed [capability Y]?"
- "If your [project] needed to support [10x current scale], which component breaks first and how would you fix it?"

FORMAT — Return ONLY a valid JSON array:
[
  {{
    "question": "specific architecture question about their project",
    "topic": "the primary architectural concept",
    "difficulty": "easy|medium|hard",
    "project_reference": "exact project name"
  }}
]

Generate the questions now:
"""


# ─────────────────────────────────────────────────────────────────────
# 4. DEBUGGING EXERCISE QUESTIONS
# ─────────────────────────────────────────────────────────────────────
DEBUGGING_EXERCISE_PROMPT = """
{anti_generic_guard}

You are a senior engineer presenting realistic debugging scenarios to the
candidate. Each scenario must be grounded in their actual project context
and tech stack — presenting bugs that COULD realistically occur.

CANDIDATE PROFILE:
- Primary Skills: {primary_skills}
- Experience Level: {experience_level}
- Domain Expertise: {domain_expertise}

PROJECTS:
{projects_json}

ADDITIONAL RESUME CONTEXT:
{resume_context}

Generate exactly {num_questions} DEBUGGING interview questions.

Each question MUST:
- Present a realistic bug or failure scenario in their project's tech stack
- Include specific symptoms (error messages, unexpected behavior, performance degradation)
- Ask for a systematic debugging approach, not just the fix
- Reference actual components from their project (database, cache, API, model, etc.)
- Test debugging METHODOLOGY, not just knowledge of the fix

QUESTION STYLES TO USE:
- "In your [project], users report [symptom]. Your [component] is running [tech]. Walk me through your debugging steps."
- "Your [project]'s [feature] suddenly starts [failure]. Logs show [clue]. What's your top 3 hypotheses and how do you verify each?"
- "After deploying a new version of [project], [metric] drops by [X%]. Given your stack of [tech list], where do you start?"

FORMAT — Return ONLY a valid JSON array:
[
  {{
    "question": "realistic debugging scenario with specific symptoms",
    "topic": "the primary technology or concept involved",
    "difficulty": "easy|medium|hard",
    "project_reference": "exact project name"
  }}
]

Generate the questions now:
"""


# ─────────────────────────────────────────────────────────────────────
# 5. PROJECT EXTRACTION PROMPT
# ─────────────────────────────────────────────────────────────────────
PROJECT_EXTRACTION_PROMPT = """
You are a technical resume analyzer. Extract ALL projects mentioned in the
resume text below into structured JSON.

RESUME TEXT:
{resume_text}

INSTRUCTIONS:
1. Identify EVERY project, application, or significant system the candidate built or contributed to.
2. For each project, extract as much detail as possible from the resume.
3. If a field is not explicitly mentioned, make a reasonable inference from context.
4. Also identify the candidate's overall primary skills, experience level, and domain expertise.

Return ONLY a valid JSON object in this exact format:
{{
  "projects": [
    {{
      "name": "Project or Application Name",
      "role": "Their role (e.g., Full-Stack Developer, ML Engineer, Backend Lead)",
      "tech_stack": ["Technology1", "Technology2", "Framework1"],
      "challenge": "The main challenge or problem they solved",
      "solution": "How they solved it — specific approach or implementation",
      "outcome": "Result or impact (metrics, improvements, deliverables)"
    }}
  ],
  "primary_skills": ["Skill1", "Skill2", "Skill3"],
  "experience_level": "junior|mid|senior",
  "domain_expertise": ["Domain1", "Domain2"]
}}

RULES:
- Extract at least 1 project, maximum 6 projects
- tech_stack should list specific technologies, not categories
- experience_level: junior = 0-2 years, mid = 2-5 years, senior = 5+ years
- If only one project is found, be extra thorough extracting details

Extract now:
"""


# ─────────────────────────────────────────────────────────────────────


# ───────────────────────────────────────────────────────────────────────
# 5. GENERAL / HR / BEHAVIORAL QUESTIONS
# ───────────────────────────────────────────────────────────────────────
GENERAL_INTERVIEW_PROMPT = """
You are a senior interviewer conducting a well-rounded mock interview.
Generate questions that test the candidate's soft skills, problem-solving approach,
communication ability, and general technical understanding.

CANDIDATE PROFILE:
- Primary Skills: {primary_skills}
- Experience Level: {experience_level}
- Domain Expertise: {domain_expertise}

ADDITIONAL RESUME CONTEXT:
{resume_context}

CANDIDATE'S TECH STACK (for reference): {projects_json}

Generate exactly {num_questions} GENERAL interview questions.

Mix these types:
- Behavioral (teamwork, conflict resolution, leadership)
- Situational (how would you handle X scenario)
- General technical (explain a concept in your own words, compare approaches)
- Career motivation (why this field, strengths/weaknesses, goals)

Each question should be:
- Answerable by any candidate at their experience level
- Open-ended (not yes/no)
- Designed to reveal thought process, not memorized definitions
- Practical and relevant to a real job interview

FORMAT — Return ONLY a valid JSON array:
[
  {{
    "question": "Tell me about a time you had to convince your team to adopt a different approach. What was the situation, and how did you handle pushback?",
    "topic": "the primary theme being assessed",
    "difficulty": "easy|medium|hard",
    "project_reference": null
  }}
]

Generate the questions now:
"""

# Helper: Get template by category
# ─────────────────────────────────────────────────────────────────────
_TEMPLATE_MAP = {
    "project_based": PROJECT_DEEP_DIVE_PROMPT,
    "challenge": CHALLENGE_SCENARIO_PROMPT,
    "architecture": ARCHITECTURE_PROBE_PROMPT,
    "debugging": DEBUGGING_EXERCISE_PROMPT,
    "general": GENERAL_INTERVIEW_PROMPT,
}


def get_template(category: str) -> str:
    """
    Return the prompt template for the given question category.

    Args:
        category: One of 'project_based', 'challenge', 'architecture', 'debugging'

    Returns:
        The prompt template string

    Raises:
        ValueError: If the category is unknown
    """
    template = _TEMPLATE_MAP.get(category)
    if template is None:
        raise ValueError(
            f"Unknown question category: {category!r}. "
            f"Valid categories: {list(_TEMPLATE_MAP.keys())}"
        )
    return template


def get_all_categories() -> list:
    """Return the list of all question categories."""
    return list(_TEMPLATE_MAP.keys())
