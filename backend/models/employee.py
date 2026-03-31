"""
Pydantic models for Employee, Payroll, Leave, Training, and related HR data.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
import uuid


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"


class LeaveType(str, Enum):
    ANNUAL = "annual"
    SICK = "sick"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    UNPAID = "unpaid"
    EMERGENCY = "emergency"


class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TrainingStatus(str, Enum):
    RECOMMENDED = "recommended"
    ENROLLED = "enrolled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# ─── Employee ─────────────────────────────────────────────────────────────────

class EmployeeCreate(BaseModel):
    full_name: str
    email: str
    department: str
    job_title: str
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    manager_id: Optional[str] = None
    start_date: date
    base_salary: float
    skills: List[str] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v.lower().strip()


class EmployeeProfile(EmployeeCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    leave_balance: Dict[str, int] = Field(
        default_factory=lambda: {
            "annual": 20, "sick": 10, "emergency": 3
        }
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


# ─── Leave ────────────────────────────────────────────────────────────────────

class LeaveRequestCreate(BaseModel):
    employee_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date, info: Any) -> date:
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class LeaveRequest(LeaveRequestCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: LeaveStatus = LeaveStatus.PENDING
    days_requested: int = 0
    approved_by: Optional[str] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


# ─── Payroll ──────────────────────────────────────────────────────────────────

class PayrollRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    period_month: int = Field(ge=1, le=12)
    period_year: int
    base_salary: float
    bonuses: float = 0.0
    deductions: float = 0.0
    tax_amount: float = 0.0
    social_security: float = 0.0
    net_salary: float
    currency: str = "USD"
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Training ─────────────────────────────────────────────────────────────────

class TrainingProgram(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    provider: str
    description: Optional[str] = None
    duration_hours: int
    skills_covered: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    cost: float = 0.0
    format: str = "online"  # online, in-person, hybrid


class TrainingRecommendation(BaseModel):
    employee_id: str
    skill_gaps: List[str]
    recommended_programs: List[TrainingProgram]
    priority: str = "medium"  # low, medium, high
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Onboarding ───────────────────────────────────────────────────────────────

class OnboardingTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    assigned_to: str  # HR, Manager, Employee, IT
    due_days: int  # days from start date
    is_completed: bool = False
    completed_at: Optional[datetime] = None


class OnboardingPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: str
    department: str
    start_date: date
    tasks: List[OnboardingTask] = Field(default_factory=list)
    welcome_message: Optional[str] = None
    buddy_assigned: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Interview ────────────────────────────────────────────────────────────────

class InterviewQuestion(BaseModel):
    question: str
    category: str  # technical, behavioral, situational
    expected_answer_hints: Optional[str] = None
    difficulty: str = "medium"  # easy, medium, hard


class InterviewPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str
    job_title: str
    scheduled_at: Optional[datetime] = None
    interviewer: Optional[str] = None
    questions: List[InterviewQuestion] = Field(default_factory=list)
    duration_minutes: int = 60
    format: str = "video"  # video, in-person, phone
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
