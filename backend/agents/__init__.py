from .cv_agent import CVAgent, cv_agent
from .interview_agent import InterviewAgent, interview_agent
from .privacy_agent import PrivacyAgent, privacy_agent
from .rh_assistant_agent import RHAssistantAgent, rh_assistant_agent
from .segula_agent import segula_agent  # RAG agent (base documentaire RH)

__all__ = [
    "CVAgent", "cv_agent",
    "InterviewAgent", "interview_agent",
    "PrivacyAgent", "privacy_agent",
    "RHAssistantAgent", "rh_assistant_agent",
    "segula_agent",
]
