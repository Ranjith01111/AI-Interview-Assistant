"""
Interview Presets — Pre-configured interview styles that mimic real company patterns.

Each preset defines:
  - Question distribution across categories
  - Difficulty level
  - Number of questions
  - Timer per question (seconds, None = no timer)
  - Whether follow-ups are enabled
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class InterviewPreset:
    """A pre-configured interview mode."""
    id: str
    name: str
    description: str
    icon: str
    distribution: Dict[str, float]  # category → percentage (0.0-1.0)
    difficulty: str  # "easy", "medium", "hard"
    num_questions: int
    timer_seconds: Optional[int]  # per-question timer, None = no timer
    follow_ups: bool = False
    tags: List[str] = field(default_factory=list)


# ── Preset Definitions ──────────────────────────────────────────────────────

PRESETS: Dict[str, InterviewPreset] = {
    "faang_hard": InterviewPreset(
        id="faang_hard",
        name="FAANG Style",
        description="Heavy DSA + System Design at hard difficulty. Mimics Google/Meta interviews.",
        icon="🏢",
        distribution={
            "data_structures": 0.35,
            "system_design": 0.30,
            "behavioral": 0.15,
            "python": 0.10,
            "api_design": 0.10,
        },
        difficulty="hard",
        num_questions=8,
        timer_seconds=90,
        follow_ups=True,
        tags=["Google", "Meta", "Amazon", "Apple"],
    ),

    "startup_practical": InterviewPreset(
        id="startup_practical",
        name="Startup Style",
        description="Practical system design + coding focus. Fast-paced, real-world problems.",
        icon="🚀",
        distribution={
            "system_design": 0.30,
            "python": 0.20,
            "javascript": 0.15,
            "behavioral": 0.20,
            "api_design": 0.15,
        },
        difficulty="medium",
        num_questions=7,
        timer_seconds=120,
        follow_ups=False,
        tags=["Startup", "Full-Stack", "Practical"],
    ),

    "fresher_friendly": InterviewPreset(
        id="fresher_friendly",
        name="Fresher Friendly",
        description="Easy questions with behavioral focus. Perfect for first-time interviews.",
        icon="🎓",
        distribution={
            "behavioral": 0.40,
            "python": 0.20,
            "data_structures": 0.20,
            "sql": 0.10,
            "git": 0.10,
        },
        difficulty="easy",
        num_questions=6,
        timer_seconds=None,  # No timer pressure for freshers
        follow_ups=False,
        tags=["Entry-Level", "Campus", "Fresher"],
    ),

    "amazon_lp": InterviewPreset(
        id="amazon_lp",
        name="Amazon LP",
        description="Leadership Principles + System Design. STAR method behavioral questions.",
        icon="📦",
        distribution={
            "behavioral": 0.50,
            "system_design": 0.25,
            "data_structures": 0.15,
            "api_design": 0.10,
        },
        difficulty="medium",
        num_questions=8,
        timer_seconds=120,
        follow_ups=True,
        tags=["Amazon", "Leadership", "STAR"],
    ),

    "frontend_specialist": InterviewPreset(
        id="frontend_specialist",
        name="Frontend Expert",
        description="React + JavaScript deep-dive with UI system design questions.",
        icon="🎨",
        distribution={
            "react": 0.35,
            "javascript": 0.30,
            "system_design": 0.15,
            "behavioral": 0.10,
            "testing": 0.10,
        },
        difficulty="medium",
        num_questions=8,
        timer_seconds=90,
        follow_ups=False,
        tags=["Frontend", "React", "UI/UX"],
    ),

    "backend_engineer": InterviewPreset(
        id="backend_engineer",
        name="Backend Engineer",
        description="APIs, databases, system design, and DevOps focus.",
        icon="⚙️",
        distribution={
            "python": 0.20,
            "sql": 0.20,
            "system_design": 0.25,
            "docker": 0.15,
            "api_design": 0.10,
            "security": 0.10,
        },
        difficulty="medium",
        num_questions=8,
        timer_seconds=90,
        follow_ups=False,
        tags=["Backend", "APIs", "Databases"],
    ),

    "quick_practice": InterviewPreset(
        id="quick_practice",
        name="Quick Practice",
        description="Short 5-question session. Mixed topics, medium difficulty. Great for daily warmup.",
        icon="⚡",
        distribution={
            "python": 0.20,
            "data_structures": 0.20,
            "system_design": 0.20,
            "behavioral": 0.20,
            "javascript": 0.20,
        },
        difficulty="medium",
        num_questions=5,
        timer_seconds=60,
        follow_ups=False,
        tags=["Quick", "Daily", "Warmup"],
    ),
}


def get_preset(preset_id: str) -> Optional[InterviewPreset]:
    """Get a preset by ID."""
    return PRESETS.get(preset_id)


def get_all_presets() -> List[Dict]:
    """Get all presets as a list of dicts (for API response)."""
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "icon": p.icon,
            "difficulty": p.difficulty,
            "num_questions": p.num_questions,
            "timer_seconds": p.timer_seconds,
            "follow_ups": p.follow_ups,
            "tags": p.tags,
            "distribution": p.distribution,
        }
        for p in PRESETS.values()
    ]


def get_categories_from_preset(preset_id: str) -> List[str]:
    """Extract the focus categories from a preset."""
    preset = get_preset(preset_id)
    if not preset:
        return []
    return list(preset.distribution.keys())


def get_question_counts_from_preset(preset_id: str) -> Dict[str, int]:
    """Get how many questions each category should have based on the preset."""
    preset = get_preset(preset_id)
    if not preset:
        return {}
    
    counts = {}
    for category, ratio in preset.distribution.items():
        counts[category] = max(1, round(preset.num_questions * ratio))
    
    # Adjust to match total
    total = sum(counts.values())
    if total > preset.num_questions:
        # Remove from the largest category
        largest = max(counts, key=counts.get)
        counts[largest] -= (total - preset.num_questions)
    elif total < preset.num_questions:
        largest = max(counts, key=counts.get)
        counts[largest] += (preset.num_questions - total)
    
    return counts
