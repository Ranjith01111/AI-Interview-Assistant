"""
Communication Evaluator — Assesses vocabulary, grammar, and fluency
from spoken responses in a conversational HR call simulation.

No external API — uses rule-based analysis + pattern matching.
"""

import re
import random
from typing import Dict, List, Tuple
from collections import Counter


# ── HR Conversation Topics (natural, phone-call style) ──────────────────
HR_CONVERSATION_FLOW = [
    {
        "phase": "greeting",
        "prompts": [
            "Hi! Thank you for taking the time to speak with me today. Could you start by telling me a bit about yourself?",
            "Hello! Great to connect with you. Why don't you give me a brief introduction about yourself?",
            "Hi there! Thanks for joining this call. I'd love to hear about your background — where are you from and what do you do?",
        ]
    },
    {
        "phase": "experience",
        "prompts": [
            "That's interesting! Can you walk me through your most recent work experience? What was your role like?",
            "Nice! Tell me about your professional journey. What kind of work have you been doing recently?",
            "Great introduction! Now, what's your current or most recent professional experience?",
        ]
    },
    {
        "phase": "motivation",
        "prompts": [
            "What motivates you in your career? What kind of work environment do you thrive in?",
            "What drives you professionally? What gets you excited about going to work?",
            "Tell me, what are you passionate about in your field? What keeps you going?",
        ]
    },
    {
        "phase": "challenge",
        "prompts": [
            "Can you describe a challenging situation you faced at work and how you handled it?",
            "Tell me about a time when things didn't go as planned. How did you deal with it?",
            "Everyone faces obstacles. Can you share a difficult professional moment and what you learned?",
        ]
    },
    {
        "phase": "teamwork",
        "prompts": [
            "How do you typically work with others? Can you share an example of a successful collaboration?",
            "Tell me about your experience working in teams. What role do you usually take?",
            "Collaboration is important. Can you describe how you communicate with colleagues on projects?",
        ]
    },
    {
        "phase": "goals",
        "prompts": [
            "Where do you see yourself in the next few years? What are your career goals?",
            "What's your vision for your professional growth? Any specific goals you're working towards?",
            "Looking ahead, what would you like to achieve in your career?",
        ]
    },
    {
        "phase": "situational",
        "prompts": [
            "If you had to explain a complex technical concept to someone non-technical, how would you approach it?",
            "Imagine you disagree with your manager's decision. How would you handle that conversation?",
            "If you were given a project with an impossible deadline, what would you do?",
        ]
    },
    {
        "phase": "closing",
        "prompts": [
            "This has been a great conversation! Is there anything else you'd like to share about yourself?",
            "We're coming to the end of our call. Any final thoughts or questions you'd like to add?",
            "Thank you for this wonderful chat! Anything else you'd like me to know about you?",
        ]
    },
]

# ── Grammar patterns to detect common errors ──────────────────────────
GRAMMAR_ISSUES = [
    (r"\bi\b(?!\s*')", "Use 'I' (capitalized) when referring to yourself"),
    (r"\bhe don't\b|\bshe don't\b|\bit don't\b", "Use 'doesn't' with he/she/it"),
    (r"\bmore better\b|\bmore faster\b|\bmore bigger\b", "Avoid double comparatives"),
    (r"\bcould of\b|\bshould of\b|\bwould of\b", "Use 'could have', 'should have', 'would have'"),
    (r"\btheir is\b|\btheir are\b", "Confusing 'their' with 'there'"),
    (r"\byour welcome\b", "Use 'you're welcome' (you are)"),
    (r"\bits a\b(?!.*\bit's)", "Consider 'it's' (it is) vs 'its' (possessive)"),
    (r"\balot\b", "Write 'a lot' as two words"),
    (r"\birregardless\b", "Use 'regardless' instead of 'irregardless'"),
    (r"\bme and\b\s+\w+\s+(went|did|are|were|have)", "Consider 'X and I' as the subject"),
    (r"\bgood\b.*\b(do|did|perform|work)\b", "Use 'well' as an adverb (did well, not did good)"),
]

# ── Vocabulary level indicators ──────────────────────────────────────
ADVANCED_VOCABULARY = [
    "consequently", "furthermore", "nevertheless", "albeit", "meticulous",
    "comprehensive", "facilitate", "implement", "optimize", "strategize",
    "collaborate", "innovative", "leverage", "articulate", "proficient",
    "paradigm", "synergy", "proactive", "initiative", "analytical",
    "scalable", "methodology", "framework", "stakeholder", "deliverable",
    "milestone", "benchmark", "iterate", "streamline", "resilient",
    "adaptable", "versatile", "autonomous", "accountability", "integrity",
]

FILLER_WORDS = [
    "um", "uh", "like", "you know", "basically", "actually", "literally",
    "sort of", "kind of", "i mean", "right", "okay so", "well",
]

# ── Transition/connector words (good communication) ──────────────────
TRANSITION_WORDS = [
    "however", "therefore", "moreover", "additionally", "consequently",
    "furthermore", "in addition", "on the other hand", "for example",
    "for instance", "in contrast", "as a result", "meanwhile",
    "specifically", "in particular", "to summarize", "in conclusion",
    "first", "second", "finally", "overall",
]


class CommunicationEvaluator:
    """Evaluates spoken responses for grammar, vocabulary, and fluency."""

    def evaluate_response(self, text: str) -> Dict:
        """
        Analyze a spoken response and return evaluation metrics.
        
        Returns:
            Dict with scores, grammar_issues, vocabulary_analysis, suggestions
        """
        if not text or len(text.strip()) < 5:
            return {
                "grammar_score": 0,
                "vocabulary_score": 0,
                "fluency_score": 0,
                "overall_score": 0,
                "grammar_issues": [],
                "vocabulary_level": "minimal",
                "filler_count": 0,
                "word_count": 0,
                "suggestions": ["Try to provide a longer, more detailed response."],
            }

        text_lower = text.lower()
        words = text_lower.split()
        word_count = len(words)
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        sentence_count = max(len(sentences), 1)

        # ── Grammar Analysis ──────────────────────────────────────
        grammar_issues = []
        for pattern, suggestion in GRAMMAR_ISSUES:
            if re.search(pattern, text_lower):
                grammar_issues.append(suggestion)

        grammar_score = max(0, 10 - len(grammar_issues) * 2)

        # ── Vocabulary Analysis ──────────────────────────────────
        unique_words = set(words)
        unique_ratio = len(unique_words) / max(word_count, 1)

        advanced_used = [w for w in ADVANCED_VOCABULARY if w in text_lower]
        transitions_used = [w for w in TRANSITION_WORDS if w in text_lower]

        vocab_score = min(10, int(
            (unique_ratio * 3) +  # Diversity
            (len(advanced_used) * 1.5) +  # Advanced words
            (len(transitions_used) * 1.0) +  # Connectors
            (2 if word_count > 30 else 0)  # Adequate length bonus
        ))

        if word_count < 10:
            vocab_level = "minimal"
        elif len(advanced_used) >= 3:
            vocab_level = "advanced"
        elif len(advanced_used) >= 1 or unique_ratio > 0.6:
            vocab_level = "intermediate"
        else:
            vocab_level = "basic"

        # ── Fluency Analysis ──────────────────────────────────────
        filler_count = sum(1 for f in FILLER_WORDS if f in text_lower)
        avg_sentence_length = word_count / sentence_count

        fluency_score = 10
        # Penalize too many fillers
        fluency_score -= min(4, filler_count)
        # Penalize very short responses
        if word_count < 15:
            fluency_score -= 3
        # Penalize very short sentences (choppy speech)
        if avg_sentence_length < 5 and sentence_count > 2:
            fluency_score -= 2
        # Bonus for good structure
        if sentence_count >= 3 and avg_sentence_length > 8:
            fluency_score += 1
        fluency_score = max(0, min(10, fluency_score))

        # ── Overall Score ──────────────────────────────────────────
        overall_score = round((grammar_score * 0.3 + vocab_score * 0.35 + fluency_score * 0.35), 1)

        # ── Suggestions ──────────────────────────────────────────
        suggestions = []
        if filler_count > 2:
            suggestions.append(f"Reduce filler words (detected {filler_count}). Pause silently instead of saying 'um' or 'like'.")
        if word_count < 20:
            suggestions.append("Try to elaborate more. Give specific examples and details.")
        if not advanced_used:
            suggestions.append("Use more professional vocabulary — words like 'implement', 'collaborate', 'optimize'.")
        if not transitions_used:
            suggestions.append("Use connecting words like 'however', 'therefore', 'for example' to structure your response.")
        if grammar_issues:
            suggestions.append(f"Grammar tip: {grammar_issues[0]}")
        if not suggestions:
            suggestions.append("Great communication! Keep using clear structure and professional vocabulary.")

        return {
            "grammar_score": grammar_score,
            "vocabulary_score": vocab_score,
            "fluency_score": fluency_score,
            "overall_score": overall_score,
            "grammar_issues": grammar_issues[:3],
            "vocabulary_level": vocab_level,
            "advanced_words_used": advanced_used,
            "transitions_used": transitions_used,
            "filler_count": filler_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "suggestions": suggestions[:4],
        }

    def get_next_prompt(self, phase_index: int) -> Tuple[str, str]:
        """Get the next conversation prompt for the given phase."""
        if phase_index >= len(HR_CONVERSATION_FLOW):
            return "closing", "Thank you so much for this conversation! It was great speaking with you."
        
        phase_data = HR_CONVERSATION_FLOW[phase_index]
        return phase_data["phase"], random.choice(phase_data["prompts"])

    def generate_acknowledgment(self, evaluation: Dict) -> str:
        """Generate a natural HR-style acknowledgment based on evaluation."""
        score = evaluation["overall_score"]
        
        if score >= 8:
            acks = [
                "Wonderful! That was very well articulated.",
                "Excellent response! Very clear and professional.",
                "Great! You communicated that beautifully.",
            ]
        elif score >= 6:
            acks = [
                "Good, thank you for sharing that.",
                "Nice! That gives me a good picture.",
                "Thank you, that's helpful to know.",
            ]
        elif score >= 4:
            acks = [
                "I see, thank you. Could you elaborate a bit more next time?",
                "Okay, thanks for that. Try to give more specific details.",
                "Got it. A bit more detail would really help paint the picture.",
            ]
        else:
            acks = [
                "Thank you. Try to speak more confidently and give fuller answers.",
                "I appreciate that. Let's try to be more descriptive in your next response.",
                "Okay. Remember, it helps to give examples and speak in complete sentences.",
            ]
        
        return random.choice(acks)

    def generate_final_report(self, all_evaluations: List[Dict]) -> Dict:
        """Generate a comprehensive communication assessment report."""
        if not all_evaluations:
            return {
                "overall_rating": "N/A",
                "average_grammar": 0,
                "average_vocabulary": 0,
                "average_fluency": 0,
                "average_overall": 0,
                "total_responses": 0,
                "key_strengths": [],
                "areas_to_improve": [],
                "recommendations": [],
            }

        avg_grammar = sum(e["grammar_score"] for e in all_evaluations) / len(all_evaluations)
        avg_vocab = sum(e["vocabulary_score"] for e in all_evaluations) / len(all_evaluations)
        avg_fluency = sum(e["fluency_score"] for e in all_evaluations) / len(all_evaluations)
        avg_overall = sum(e["overall_score"] for e in all_evaluations) / len(all_evaluations)
        total_fillers = sum(e["filler_count"] for e in all_evaluations)
        total_words = sum(e["word_count"] for e in all_evaluations)

        # Rating
        if avg_overall >= 8:
            rating = "Excellent Communicator"
        elif avg_overall >= 6:
            rating = "Good Communicator"
        elif avg_overall >= 4:
            rating = "Average — Needs Practice"
        else:
            rating = "Needs Significant Improvement"

        # Strengths
        strengths = []
        if avg_grammar >= 8:
            strengths.append("Strong grammar and sentence construction")
        if avg_vocab >= 7:
            strengths.append("Good professional vocabulary usage")
        if avg_fluency >= 7:
            strengths.append("Fluent and natural speaking style")
        if total_words / max(len(all_evaluations), 1) > 40:
            strengths.append("Provides detailed, thorough responses")
        if not strengths:
            strengths.append("Willing to engage in conversation")

        # Areas to improve
        improvements = []
        if avg_grammar < 6:
            improvements.append("Work on grammar accuracy — practice sentence structure")
        if avg_vocab < 5:
            improvements.append("Expand professional vocabulary — learn 5 new words daily")
        if avg_fluency < 6:
            improvements.append("Reduce filler words — practice pausing instead")
        if total_words / max(len(all_evaluations), 1) < 20:
            improvements.append("Give longer, more detailed responses with examples")
        if not improvements:
            improvements.append("Continue practicing to maintain your skills")

        # Recommendations
        recommendations = [
            "Practice speaking for 2-3 minutes on a topic without filler words",
            "Record yourself answering common questions and listen back",
            "Read professional articles aloud to improve vocabulary",
            "Use the STAR method (Situation, Task, Action, Result) for structured answers",
        ]

        return {
            "overall_rating": rating,
            "average_grammar": round(avg_grammar, 1),
            "average_vocabulary": round(avg_vocab, 1),
            "average_fluency": round(avg_fluency, 1),
            "average_overall": round(avg_overall, 1),
            "total_responses": len(all_evaluations),
            "total_words_spoken": total_words,
            "total_filler_words": total_fillers,
            "key_strengths": strengths,
            "areas_to_improve": improvements,
            "recommendations": recommendations[:3],
        }


# Singleton
_evaluator = None

def get_communication_evaluator() -> CommunicationEvaluator:
    global _evaluator
    if _evaluator is None:
        _evaluator = CommunicationEvaluator()
    return _evaluator
