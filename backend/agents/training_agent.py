"""
Training Agent: Analyzes employee skill gaps and recommends training programs.
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# Training catalog
TRAINING_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "t001",
        "name": "Python for Data Science",
        "provider": "Coursera",
        "description": "Comprehensive Python programming with focus on data analysis.",
        "duration_hours": 40,
        "skills_covered": ["python", "pandas", "numpy", "data science"],
        "url": "https://www.coursera.org/specializations/python",
        "cost": 49.0,
        "format": "online",
        "level": "beginner",
    },
    {
        "id": "t002",
        "name": "Machine Learning A-Z",
        "provider": "Udemy",
        "description": "Learn Machine Learning and Deep Learning with Python.",
        "duration_hours": 44,
        "skills_covered": ["machine learning", "deep learning", "scikit-learn", "tensorflow"],
        "url": "https://www.udemy.com/course/machinelearning/",
        "cost": 19.99,
        "format": "online",
        "level": "intermediate",
    },
    {
        "id": "t003",
        "name": "LangChain & LLM Development",
        "provider": "DeepLearning.AI",
        "description": "Build LLM-powered applications using LangChain.",
        "duration_hours": 8,
        "skills_covered": ["langchain", "llm", "rag", "ai", "python"],
        "url": "https://www.deeplearning.ai/short-courses/",
        "cost": 0,
        "format": "online",
        "level": "intermediate",
    },
    {
        "id": "t004",
        "name": "AWS Cloud Practitioner",
        "provider": "AWS Training",
        "description": "Foundation-level AWS cloud certification preparation.",
        "duration_hours": 20,
        "skills_covered": ["aws", "cloud", "devops"],
        "url": "https://aws.amazon.com/training/",
        "cost": 0,
        "format": "online",
        "level": "beginner",
    },
    {
        "id": "t005",
        "name": "Docker & Kubernetes Masterclass",
        "provider": "Udemy",
        "description": "Master containerization and orchestration.",
        "duration_hours": 22,
        "skills_covered": ["docker", "kubernetes", "devops", "microservices"],
        "url": "https://www.udemy.com/course/docker-kubernetes-the-practical-guide/",
        "cost": 19.99,
        "format": "online",
        "level": "intermediate",
    },
    {
        "id": "t006",
        "name": "React - The Complete Guide",
        "provider": "Udemy",
        "description": "Learn React.js from scratch including hooks and context.",
        "duration_hours": 48,
        "skills_covered": ["react", "javascript", "typescript", "frontend"],
        "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/",
        "cost": 19.99,
        "format": "online",
        "level": "beginner",
    },
    {
        "id": "t007",
        "name": "Leadership and Management",
        "provider": "LinkedIn Learning",
        "description": "Develop leadership skills for engineering managers.",
        "duration_hours": 15,
        "skills_covered": ["leadership", "management", "communication", "agile"],
        "url": "https://www.linkedin.com/learning/",
        "cost": 29.99,
        "format": "online",
        "level": "intermediate",
    },
    {
        "id": "t008",
        "name": "Advanced NLP with Transformers",
        "provider": "HuggingFace",
        "description": "Deep dive into transformer models and fine-tuning.",
        "duration_hours": 12,
        "skills_covered": ["nlp", "transformers", "bert", "gpt", "huggingface", "python"],
        "url": "https://huggingface.co/learn/nlp-course/",
        "cost": 0,
        "format": "online",
        "level": "advanced",
    },
    {
        "id": "t009",
        "name": "FastAPI for Production APIs",
        "provider": "TestDriven.io",
        "description": "Build production-ready REST APIs with FastAPI.",
        "duration_hours": 10,
        "skills_covered": ["fastapi", "python", "rest api", "docker"],
        "url": "https://testdriven.io/courses/tdd-fastapi/",
        "cost": 49.0,
        "format": "online",
        "level": "intermediate",
    },
    {
        "id": "t010",
        "name": "Communication Skills for Tech Professionals",
        "provider": "Coursera",
        "description": "Improve technical communication and presentation skills.",
        "duration_hours": 8,
        "skills_covered": ["communication", "presentation", "writing"],
        "url": "https://www.coursera.org/",
        "cost": 0,
        "format": "online",
        "level": "beginner",
    },
]


class TrainingAgent:
    """
    Analyzes employee skill gaps and recommends appropriate training programs.
    """

    def analyze_and_recommend(
        self,
        employee_id: str,
        current_skills: List[str],
        job_title: str = "",
        required_skills: Optional[List[str]] = None,
        career_goal: Optional[str] = None,
        max_recommendations: int = 5,
    ) -> Dict[str, Any]:
        """
        Identify skill gaps and recommend training programs.
        """
        logger.info(f"Analyzing training needs for employee {employee_id}")

        current_lower = [s.lower() for s in current_skills]

        # Determine required skills based on job title if not provided
        if not required_skills:
            required_skills = self._get_required_skills(job_title, career_goal)

        required_lower = [r.lower() for r in required_skills]

        # Identify gaps
        skill_gaps = [
            r for r in required_lower
            if not any(c in r or r in c for c in current_lower)
        ]

        logger.info(f"Skill gaps identified: {skill_gaps}")

        # Find matching courses
        recommendations = self._find_courses(skill_gaps, current_lower, max_recommendations)

        # Prioritize
        priority = "high" if len(skill_gaps) > 3 else "medium" if len(skill_gaps) > 1 else "low"

        return {
            "employee_id": employee_id,
            "current_skills": current_skills,
            "skill_gaps": skill_gaps,
            "total_gaps": len(skill_gaps),
            "priority": priority,
            "recommended_programs": recommendations,
            "total_hours": sum(c.get("duration_hours", 0) for c in recommendations),
            "estimated_cost": sum(c.get("cost", 0) for c in recommendations),
            "learning_path": self._create_learning_path(recommendations),
            "message": (
                f"Found {len(skill_gaps)} skill gaps. "
                f"Recommended {len(recommendations)} training programs "
                f"({sum(c.get('duration_hours', 0) for c in recommendations)} hours total)."
            ),
        }

    def _get_required_skills(self, job_title: str, career_goal: Optional[str]) -> List[str]:
        """Map job title to required skill set."""
        title_lower = (job_title + " " + (career_goal or "")).lower()

        if any(t in title_lower for t in ["data scientist", "ml", "ai", "machine learning"]):
            return ["python", "machine learning", "deep learning", "nlp", "sql", "statistics"]
        elif any(t in title_lower for t in ["devops", "sre", "platform"]):
            return ["docker", "kubernetes", "aws", "linux", "ci/cd", "terraform"]
        elif any(t in title_lower for t in ["frontend", "react", "vue", "angular"]):
            return ["react", "typescript", "javascript", "css", "rest api"]
        elif any(t in title_lower for t in ["backend", "api", "python dev"]):
            return ["python", "fastapi", "docker", "postgresql", "rest api"]
        elif any(t in title_lower for t in ["manager", "lead", "principal"]):
            return ["leadership", "agile", "communication", "project management"]
        else:
            return ["python", "git", "docker", "communication", "agile"]

    def _find_courses(
        self,
        skill_gaps: List[str],
        current_skills: List[str],
        max_count: int,
    ) -> List[Dict[str, Any]]:
        """Score and rank training programs by relevance to skill gaps."""
        scored: List[tuple] = []

        for course in TRAINING_CATALOG:
            course_skills = course["skills_covered"]
            # Count how many gaps this course addresses
            gap_hits = sum(
                1 for gap in skill_gaps
                if any(gap in cs or cs in gap for cs in course_skills)
            )
            # Penalize courses teaching skills the employee already has
            redundancy = sum(
                1 for cs in course_skills
                if any(cs in curr or curr in cs for curr in current_skills)
            )
            relevance = gap_hits * 3 - redundancy
            if relevance > 0:
                scored.append((relevance, course))

        # Sort by relevance
        scored.sort(key=lambda x: x[0], reverse=True)
        return [course for _, course in scored[:max_count]]

    @staticmethod
    def _create_learning_path(courses: List[Dict[str, Any]]) -> List[str]:
        """Order courses by level for a logical learning path."""
        order = {"beginner": 0, "intermediate": 1, "advanced": 2}
        sorted_courses = sorted(courses, key=lambda c: order.get(c.get("level", "intermediate"), 1))
        return [
            f"Step {i+1}: {c['name']} ({c['duration_hours']}h) – {c['level'].title()}"
            for i, c in enumerate(sorted_courses)
        ]


training_agent = TrainingAgent()
