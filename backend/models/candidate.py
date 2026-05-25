"""
Pydantic models for Candidate and CV-related data structures.
Used across the entire platform for type safety and validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class CandidateStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    HIRED = "hired"
    REJECTED = "rejected"


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Skill(BaseModel):
    name: str
    level: Optional[SkillLevel] = None
    years: Optional[float] = None


class Education(BaseModel):
    degree: Optional[str] = None
    field: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[int] = None
    gpa: Optional[float] = None


class Experience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class GitHubProfile(BaseModel):
    username: Optional[str] = None
    url: Optional[str] = None
    public_repos: int = 0
    followers: int = 0
    stars_total: int = 0
    top_languages: List[str] = Field(default_factory=list)
    contribution_score: float = 0.0


class CandidateScore(BaseModel):
    total_score: float = Field(ge=0, le=100)
    skills_score: float = Field(ge=0, le=100)
    experience_score: float = Field(ge=0, le=100)
    education_score: float = Field(ge=0, le=100)
    github_score: float = Field(ge=0, le=100)
    communication_score: float = Field(ge=0, le=100)
    rank: Optional[int] = None
    scored_at: datetime = Field(default_factory=datetime.utcnow)
    scoring_notes: List[str] = Field(default_factory=list)


class CandidateCreate(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    job_title_applied: Optional[str] = None
    years_experience: Optional[float] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v.lower().strip()


class CandidateProfile(CandidateCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: CandidateStatus = CandidateStatus.PENDING
    skills: List[Skill] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    raw_text: Optional[str] = None
    cv_file_path: Optional[str] = None
    github_profile: Optional[GitHubProfile] = None
    score: Optional[CandidateScore] = None
    offer_evaluations: List[Dict[str, Any]] = Field(default_factory=list, description="List of LLM evaluations specific to Job Offers")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class CVDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str
    original_filename: str
    file_path: str
    file_size_bytes: int
    mime_type: str
    ocr_text: Optional[str] = None
    parsed_at: Optional[datetime] = None
    ocr_confidence: Optional[float] = None
    page_count: int = 1
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class CandidateRanking(BaseModel):
    rank: int
    candidate_id: str
    full_name: str
    email: str
    total_score: float
    top_skills: List[str]
    years_experience: Optional[float]
    status: str
    job_title_applied: Optional[str]
