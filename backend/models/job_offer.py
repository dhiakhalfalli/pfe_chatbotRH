from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class JobCriteria(BaseModel):
    must_have_skills: List[str] = Field(default_factory=list, description="List of exact skills the candidate must possess.")
    nice_to_have_skills: List[str] = Field(default_factory=list)
    min_years_experience: float = Field(default=0.0)
    education_level_required: Optional[str] = None
    languages_required: List[str] = Field(default_factory=list)
    other_requirements: List[str] = Field(default_factory=list, description="Any other specific constraints, e.g. 'Must have worked with cloud architecture'")

class JobOfferBase(BaseModel):
    title: str = Field(..., description="Job Title, e.g. Senior Frontend Developer")
    department: Optional[str] = None
    description: str = Field(..., description="Full text description of the job")
    criteria: JobCriteria

class JobOfferCreate(JobOfferBase):
    pass

class JobOffer(JobOfferBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
