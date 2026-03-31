"""
Interview Agent: Generates interview questions, schedules interviews,
and provides structured evaluation guidance.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from backend.tools.calendar_tool import calendar_tool


# Question bank organized by category and skill
QUESTION_BANK: Dict[str, List[Dict[str, Any]]] = {
    "behavioral": [
        {
            "question": "Tell me about a time you faced a significant technical challenge. How did you overcome it?",
            "category": "behavioral",
            "difficulty": "medium",
            "hints": "Look for problem-solving process, persistence, and outcome.",
        },
        {
            "question": "Describe a situation where you had to collaborate with a difficult team member.",
            "category": "behavioral",
            "difficulty": "medium",
            "hints": "Assess communication, empathy, and conflict resolution.",
        },
        {
            "question": "Give an example of a project where you had to meet a tight deadline.",
            "category": "behavioral",
            "difficulty": "medium",
            "hints": "Look for prioritization, time management, and delivery.",
        },
    ],
    "leadership": [
        {
            "question": "Describe your experience leading a team. What was the biggest challenge?",
            "category": "leadership",
            "difficulty": "hard",
            "hints": "Assess team management, decision-making, and mentorship.",
        },
        {
            "question": "How do you handle disagreements with your manager?",
            "category": "leadership",
            "difficulty": "medium",
            "hints": "Look for professionalism and constructive communication.",
        },
    ],
    "python": [
        {
            "question": "Explain the difference between `*args` and `**kwargs` in Python.",
            "category": "technical",
            "difficulty": "easy",
            "hints": "args: positional tuple, kwargs: keyword dict.",
        },
        {
            "question": "What are Python decorators and how do you use them?",
            "category": "technical",
            "difficulty": "medium",
            "hints": "Higher-order functions, @syntax, closures.",
        },
        {
            "question": "Explain the GIL and how async/await helps work around it.",
            "category": "technical",
            "difficulty": "hard",
            "hints": "GIL blocking threads, asyncio cooperates.",
        },
    ],
    "machine_learning": [
        {
            "question": "What is the difference between supervised and unsupervised learning?",
            "category": "technical",
            "difficulty": "easy",
            "hints": "Labeled vs unlabeled data, specific tasks.",
        },
        {
            "question": "Explain overfitting and how to prevent it.",
            "category": "technical",
            "difficulty": "medium",
            "hints": "Regularization, dropout, cross-validation, more data.",
        },
        {
            "question": "How does attention mechanism work in transformer models?",
            "category": "technical",
            "difficulty": "hard",
            "hints": "Q, K, V matrices, scaled dot-product, multi-head.",
        },
    ],
    "general": [
        {
            "question": "Why are you interested in this position?",
            "category": "motivational",
            "difficulty": "easy",
            "hints": "Look for genuine interest and alignment with company values.",
        },
        {
            "question": "Where do you see yourself in 5 years?",
            "category": "motivational",
            "difficulty": "easy",
            "hints": "Assess ambition, growth mindset, and commitment.",
        },
        {
            "question": "What are your greatest strengths and one area for improvement?",
            "category": "motivational",
            "difficulty": "easy",
            "hints": "Self-awareness and growth mindset.",
        },
    ],
}


class InterviewAgent:
    """
    Generates customized interview question sets and manages scheduling.
    """

    def generate_questions(
        self,
        candidate_id: str,
        skills: List[str],
        job_title: str = "",
        experience_years: float = 0,
        num_questions: int = 10,
    ) -> Dict[str, Any]:
        """
        Generate a tailored set of interview questions based on candidate profile.
        """
        logger.info(f"Generating interview questions for candidate {candidate_id}")

        questions: List[Dict[str, Any]] = []
        skills_lower = [s.lower() for s in skills]

        # Always include behavioral questions
        questions.extend(
            self._pick_questions("behavioral", 2)
        )

        # Add general/motivational
        questions.extend(
            self._pick_questions("general", 2)
        )

        # Add skill-specific technical questions
        tech_added = 0
        target_tech = num_questions - 4  # Remaining slots for technical

        for skill_key in QUESTION_BANK:
            if tech_added >= target_tech:
                break
            # Match skill keywords to question bank categories
            if any(skill_key in s or s in skill_key for s in skills_lower):
                skill_qs = self._pick_questions(
                    skill_key,
                    min(3, target_tech - tech_added),
                    difficulty=self._map_difficulty(experience_years)
                )
                questions.extend(skill_qs)
                tech_added += len(skill_qs)

        # Fill remaining with ML/Python if not enough
        if len(questions) < num_questions:
            for fallback in ["python", "machine_learning", "leadership"]:
                remaining = num_questions - len(questions)
                if remaining <= 0:
                    break
                questions.extend(self._pick_questions(fallback, remaining))

        questions = questions[:num_questions]

        return {
            "candidate_id": candidate_id,
            "job_title": job_title,
            "total_questions": len(questions),
            "questions": questions,
            "instructions": (
                f"Interview plan for {job_title} position | "
                f"Duration: {len(questions) * 5}-{len(questions) * 8} minutes | "
                f"Candidate experience: {experience_years:.0f}+ years"
            ),
            "evaluation_criteria": [
                "Technical accuracy and depth",
                "Problem-solving approach",
                "Communication clarity",
                "Cultural fit and attitude",
                "Learning mindset",
            ],
        }

    def schedule(
        self,
        candidate_id: str,
        candidate_name: str,
        interviewer: str,
        preferred_date: Optional[datetime] = None,
        duration_minutes: int = 60,
        format_type: str = "video",
    ) -> Dict[str, Any]:
        """Schedule an interview and return event details."""
        if preferred_date is None:
            # Default to next business day at 10 AM
            now = datetime.now()
            days_ahead = 1
            if now.weekday() >= 4:  # Friday = 4
                days_ahead = 7 - now.weekday()
            preferred_date = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)

        event = calendar_tool.schedule_interview(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            interviewer=interviewer,
            scheduled_at=preferred_date,
            duration_minutes=duration_minutes,
            format_type=format_type,
        )

        return {
            "event": event,
            "confirmation": f"✅ Interview scheduled for {candidate_name} on {preferred_date.strftime('%A, %B %d %Y at %H:%M')}",
            "format": format_type,
            "duration": f"{duration_minutes} minutes",
            "interviewer": interviewer,
        }

    def _pick_questions(
        self,
        category: str,
        count: int,
        difficulty: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Pick questions from a category, optionally filtered by difficulty."""
        pool = QUESTION_BANK.get(category, [])
        if difficulty:
            pool = [q for q in pool if q.get("difficulty") == difficulty] or pool
        return pool[:count]

    @staticmethod
    def _map_difficulty(years_exp: float) -> str:
        if years_exp < 2:
            return "easy"
        elif years_exp < 5:
            return "medium"
        else:
            return "hard"


interview_agent = InterviewAgent()
