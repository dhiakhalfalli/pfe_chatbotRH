"""
Interview Agent: Generates interview questions using LLM (Groq/Ollama),
schedules interviews, and provides structured evaluation guidance.
Falls back to a static question bank when no LLM is available.
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from backend.services.llm_service import generate_response


# ── Static question bank (fallback when LLM is unavailable) ───────────────────

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
    ],
}


class InterviewAgent:
    """
    Generates customized interview question sets using LLM.
    Falls back to static question bank when LLM is unavailable.
    """

    def generate_questions(
        self,
        candidate_id: str,
        skills: List[str],
        job_title: str = "",
        experience_years: float = 0,
        num_questions: int = 10,
        candidate_name: str = "",
        candidate_summary: str = "",
    ) -> Dict[str, Any]:
        """
        Generate a tailored set of interview questions based on candidate profile.
        Uses LLM for intelligent generation, falls back to static bank.
        """
        logger.info(f"Generating interview questions for candidate {candidate_id}, job: {job_title}")

        # ── Try LLM-based generation first ────────────────────────────────────
        llm_result = self._generate_with_llm(
            skills=skills,
            job_title=job_title,
            experience_years=experience_years,
            num_questions=num_questions,
            candidate_name=candidate_name,
            candidate_summary=candidate_summary,
        )

        if llm_result:
            llm_result["candidate_id"] = candidate_id
            return llm_result

        # ── Fallback: static question bank ────────────────────────────────────
        logger.warning("LLM unavailable, using static question bank fallback")
        return self._generate_static(candidate_id, skills, job_title, experience_years, num_questions)

    def _generate_with_llm(
        self,
        skills: List[str],
        job_title: str,
        experience_years: float,
        num_questions: int,
        candidate_name: str = "",
        candidate_summary: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Generate questions using LLM (Groq or Ollama)."""

        difficulty_level = "junior" if experience_years < 2 else ("mid-level" if experience_years < 5 else "senior")
        skills_str = ", ".join(skills) if skills else "non spécifié"
        title = job_title or "Software Engineer"

        system_prompt = (
            "You are an expert HR interviewer and technical recruiter. "
            "You generate high-quality, targeted interview questions for specific positions. "
            "Your questions must be directly relevant to the job title, required skills, and candidate experience level. "
            "Always respond in valid JSON format. Never include any text outside the JSON."
        )

        candidate_context = ""
        if candidate_name:
            candidate_context += f"\n- Candidate name: {candidate_name}"
        if candidate_summary:
            candidate_context += f"\n- Candidate summary: {candidate_summary}"

        user_prompt = f"""Generate exactly {num_questions} interview questions for this position:

- Job title: {title}
- Required skills: {skills_str}
- Experience level: {difficulty_level} ({experience_years:.0f} years)
{candidate_context}

Requirements:
1. Include 2-3 behavioral/soft-skill questions
2. Include {num_questions - 3} technical questions SPECIFIC to the skills listed above
3. Questions must be appropriate for the experience level
4. Each question must have a category, difficulty, and evaluation hints
5. Technical questions should test real practical knowledge, not just theory
6. DO NOT include generic questions like "What are your strengths?" — focus on role-specific questions

Respond ONLY with this JSON format (no other text):
{{
  "job_title": "{title}",
  "total_questions": {num_questions},
  "questions": [
    {{
      "question": "Your specific question here",
      "category": "technical|behavioral|situational|system_design",
      "difficulty": "easy|medium|hard",
      "hints": "What the interviewer should look for in the answer"
    }}
  ],
  "instructions": "Interview plan summary in one line",
  "evaluation_criteria": ["criterion 1", "criterion 2", "criterion 3", "criterion 4", "criterion 5"]
}}"""

        try:
            response = generate_response(system_prompt, user_prompt)
            if not response:
                return None

            # Parse JSON from LLM response
            result = self._parse_llm_json(response)
            if result and "questions" in result:
                logger.info(f"LLM generated {len(result['questions'])} interview questions for {title}")
                return result

            logger.warning("LLM response could not be parsed as valid JSON")
            return None

        except Exception as e:
            logger.error(f"LLM interview generation failed: {e}")
            return None

    @staticmethod
    def _parse_llm_json(text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from LLM response, handling markdown code blocks."""
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding first { to last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        return None

    def _generate_static(
        self,
        candidate_id: str,
        skills: List[str],
        job_title: str,
        experience_years: float,
        num_questions: int,
    ) -> Dict[str, Any]:
        """Fallback: pick from the static question bank."""
        questions: List[Dict[str, Any]] = []

        # Behavioral
        questions.extend(self._pick_questions("behavioral", 2))

        # General/motivational
        questions.extend(self._pick_questions("general", 2))

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

    # Note: La planification d'entretien est gérée via l'interface utilisateur.

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
