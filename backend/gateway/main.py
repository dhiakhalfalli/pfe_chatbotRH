"""
FastAPI Gateway: Main API entry point for the HR Multi-Agent Platform.
Handles CV uploads, chatbot queries, leave requests, and HR operations.
"""
import logging
import os
import uuid
import shutil
import json
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pathlib import Path

import uvicorn
from fastapi import (
    FastAPI, File, UploadFile, HTTPException, Depends,
    BackgroundTasks, Query, Form, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config.settings import settings
from backend.database.mongo import MongoDB
from backend.database.mysql import init_sql_db, get_sql_db
from backend.orchestrator.graph import orchestrator
from backend.agents.cv_agent import cv_agent
from backend.agents.interview_agent import interview_agent
from backend.agents.onboarding_agent import onboarding_agent
from backend.agents.training_agent import training_agent
from backend.models.candidate import CandidateCreate, CandidateRanking
from backend.models.employee import EmployeeCreate, LeaveRequestCreate

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-Agent Intelligent HR Chatbot Platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Startup / Shutdown ───────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info("🚀 Starting HR Platform API...")
    await MongoDB.connect()
    init_sql_db()
    os.makedirs(settings.CV_UPLOAD_DIR, exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    logger.info(f"✅ API ready at http://0.0.0.0:8000")


@app.on_event("shutdown")
async def shutdown():
    await MongoDB.disconnect()
    logger.info("API shut down")


# ─── Request / Response Models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    employee_id: Optional[str] = None
    candidate_id: Optional[str] = None
    thread_id: str = "default"
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    intent: str
    agent: str
    response: str
    data: Optional[Dict[str, Any]] = None
    query: str


class LeaveRequestBody(BaseModel):
    employee_id: str
    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None


class EmployeeCreateRequest(BaseModel):
    full_name: str
    email: str
    department: str
    job_title: str
    start_date: date
    base_salary: float
    skills: List[str] = []


class OnboardingRequest(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    job_title: str
    start_date: date
    manager_name: Optional[str] = None


class TrainingRequest(BaseModel):
    employee_id: str
    current_skills: List[str]
    job_title: str = ""
    required_skills: Optional[List[str]] = None
    career_goal: Optional[str] = None


class InterviewRequest(BaseModel):
    candidate_id: str
    skills: List[str]
    job_title: str = ""
    experience_years: float = 0
    num_questions: int = 10


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─── CV Upload & Analysis ─────────────────────────────────────────────────────

@app.post("/upload_cv", tags=["CV"])
async def upload_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_title: Optional[str] = Form(None),
    required_skills: Optional[str] = Form(None),
):
    """
    Upload a CV (PDF/image) and trigger async processing pipeline.
    Returns candidate profile with score.
    """
    # Validate file type
    allowed_types = {"application/pdf", "image/png", "image/jpeg"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, PNG, JPEG"
        )

    # Validate file size
    content = await file.read()
    max_size = settings.MAX_CV_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_CV_SIZE_MB}MB"
        )

    # Save to disk
    upload_dir = Path(settings.CV_UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = upload_dir / safe_name
    file_path.write_bytes(content)

    # Parse required skills
    skills_list = None
    if required_skills:
        skills_list = [s.strip() for s in required_skills.split(",") if s.strip()]

    # Process CV (synchronously for immediate response)
    try:
        result = await cv_agent.process_cv(
            str(file_path),
            file.filename,
            len(content),
            job_title,
            skills_list,
        )
    except Exception as e:
        logger.error(f"CV processing error: {e}")
        raise HTTPException(status_code=500, detail=f"CV processing failed: {str(e)}")

    return JSONResponse(
        status_code=201,
        content={
            "message": "CV processed successfully",
            "candidate_id": result.get("candidate_id"),
            "status": result.get("status"),
            "score": result.get("score"),
            "pipeline_steps": result.get("pipeline_steps"),
            "candidate": result.get("candidate"),
        }
    )


# ─── HR Chatbot ───────────────────────────────────────────────────────────────

@app.post("/query_hr", response_model=ChatResponse, tags=["Chatbot"])
async def query_hr(request: ChatRequest):
    """
    Main chatbot endpoint: routes queries to specialized AI agents.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        result = await orchestrator.process(
            query=request.query,
            employee_id=request.employee_id,
            candidate_id=request.candidate_id,
            metadata=request.metadata,
            thread_id=request.thread_id,
        )
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

    # Extract human-readable response
    result_data = result.get("result", {})
    
    # Generate markdown response if not strictly given
    if result_data.get("response"):
        response_text = result_data.get("response")
    elif result_data.get("message"):
        response_text = result_data.get("message")
    elif result_data.get("confirmation"):
        response_text = result_data.get("confirmation")
    elif "questions" in result_data:
        # Interview Agent Formatting
        response_text = f"**{result_data.get('instructions', 'Interview Plan')}**\n\n"
        for i, q in enumerate(result_data["questions"]):
            response_text += f"{i+1}. **{q.get('question', '')}**\n"
            response_text += f"   *Category:* {q.get('category', '')} | *Difficulty:* {q.get('difficulty', '')}\n"
            response_text += f"   *Hints:* {q.get('hints', '')}\n\n"
        if "evaluation_criteria" in result_data:
            response_text += "**Evaluation Criteria:**\n" + "\n".join(f"- {c}" for c in result_data["evaluation_criteria"])
    elif "tasks" in result_data and "welcome_message" in result_data:
        # Onboarding Agent Formatting
        response_text = f"{result_data['welcome_message']}\n\n**Onboarding Tasks:**\n\n"
        for i, t in enumerate(result_data["tasks"]):
            response_text += f"{i+1}. **{t.get('title', '')}** (Due Day {t.get('due_day', 1)})\n   {t.get('description', '')}\n\n"
    elif "recommended_courses" in result_data:
        # Training Agent Formatting
        response_text = f"**Skill Gaps Identified:** {', '.join(result_data.get('skill_gaps', []))}\n\n**Recommended Training:**\n\n"
        for i, c in enumerate(result_data["recommended_courses"]):
            response_text += f"{i+1}. **{c.get('title', '')}** ({c.get('provider', '')})\n   *Level:* {c.get('level', '')} | *Duration:* {c.get('duration_hours', '')}h\n\n"
    else:
        response_text = json.dumps(result_data, indent=2, default=str)

    return ChatResponse(
        intent=result.get("intent", "unknown"),
        agent=result.get("agent", ""),
        response=response_text,
        data=result_data,
        query=request.query,
    )


# ─── Leave Management ─────────────────────────────────────────────────────────

@app.post("/leave_request", tags=["Leave"])
async def submit_leave_request(request: LeaveRequestBody):
    """Submit a new leave request."""
    from backend.agents.leave_agent import leave_agent

    result = leave_agent.handle_request(
        action="submit",
        employee_id=request.employee_id,
        leave_type=request.leave_type,
        start_date=request.start_date,
        end_date=request.end_date,
        reason=request.reason,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("response"))

    return result


@app.get("/leave_balance/{employee_id}", tags=["Leave"])
async def check_leave_balance(employee_id: str):
    """Check leave balance for an employee."""
    from backend.agents.leave_agent import leave_agent
    return leave_agent.check_balance(employee_id, None)


# ─── Candidate Ranking ────────────────────────────────────────────────────────

@app.get("/candidate_ranking", tags=["Recruitment"])
async def get_candidate_ranking(
    limit: int = Query(default=20, ge=1, le=100),
    job_title: Optional[str] = Query(default=None),
):
    """Get ranked list of candidates by total score."""
    try:
        candidates = await MongoDB.get_ranked_candidates(limit=limit, job_title=job_title)
    except Exception as e:
        logger.error(f"Ranking query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    ranked = []
    for i, c in enumerate(candidates):
        score = c.get("score") or {}
        skills = c.get("skills", [])
        top_skills = [
            s["name"] if isinstance(s, dict) else s
            for s in skills[:5]
        ]
        ranked.append({
            "rank": i + 1,
            "candidate_id": c.get("id"),
            "full_name": c.get("full_name", "Unknown"),
            "email": c.get("email"),
            "total_score": score.get("total_score", 0),
            "skills_score": score.get("skills_score", 0),
            "experience_score": score.get("experience_score", 0),
            "education_score": score.get("education_score", 0),
            "top_skills": top_skills,
            "years_experience": c.get("years_experience"),
            "status": c.get("status", "pending"),
            "job_title_applied": c.get("job_title_applied"),
        })

    return {"total": len(ranked), "candidates": ranked}


# ─── Employee Profile ─────────────────────────────────────────────────────────

@app.get("/employee_profile/{employee_id}", tags=["Employees"])
async def get_employee_profile(employee_id: str):
    """Get complete employee profile."""
    db = get_sql_db()
    emp = db.get_employee(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return emp


@app.post("/employee", tags=["Employees"], status_code=201)
async def create_employee(request: EmployeeCreateRequest):
    """Create a new employee record."""
    emp_id = str(uuid.uuid4())
    db = get_sql_db()
    emp_data = {
        "id": emp_id,
        "full_name": request.full_name,
        "email": request.email,
        "department": request.department,
        "job_title": request.job_title,
        "start_date": request.start_date,
        "base_salary": request.base_salary,
        "skills": request.skills,
        "is_active": True,
    }
    db.insert_employee(emp_data)
    return {"message": "Employee created", "employee_id": emp_id}


@app.get("/employees", tags=["Employees"])
async def list_employees(department: Optional[str] = Query(None)):
    """List all active employees."""
    db = get_sql_db()
    return {"employees": db.list_employees(department)}


# ─── Onboarding ───────────────────────────────────────────────────────────────

@app.post("/onboarding", tags=["HR Processes"])
async def create_onboarding(request: OnboardingRequest):
    """Generate an onboarding plan for a new employee."""
    plan = onboarding_agent.create_onboarding_plan(
        employee_id=request.employee_id,
        employee_name=request.employee_name,
        department=request.department,
        job_title=request.job_title,
        start_date=request.start_date,
        manager_name=request.manager_name,
    )
    return plan


# ─── Training ─────────────────────────────────────────────────────────────────

@app.post("/training_recommendations", tags=["HR Processes"])
async def get_training_recommendations(request: TrainingRequest):
    """Get training recommendations for an employee."""
    return training_agent.analyze_and_recommend(
        employee_id=request.employee_id,
        current_skills=request.current_skills,
        job_title=request.job_title,
        required_skills=request.required_skills,
        career_goal=request.career_goal,
    )


# ─── Interview ────────────────────────────────────────────────────────────────

@app.post("/interview_questions", tags=["Recruitment"])
async def generate_interview_questions(request: InterviewRequest):
    """Generate tailored interview questions for a candidate."""
    return interview_agent.generate_questions(
        candidate_id=request.candidate_id,
        skills=request.skills,
        job_title=request.job_title,
        experience_years=request.experience_years,
        num_questions=request.num_questions,
    )


# ─── Candidates ───────────────────────────────────────────────────────────────

@app.get("/candidates", tags=["Recruitment"])
async def list_candidates(
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
):
    """List all candidates."""
    try:
        candidates = await MongoDB.list_candidates(limit=limit, skip=skip)
        return {"total": len(candidates), "candidates": candidates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candidates/{candidate_id}", tags=["Recruitment"])
async def get_candidate(candidate_id: str):
    """Get a specific candidate by ID."""
    candidate = await MongoDB.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@app.patch("/candidates/{candidate_id}", tags=["Recruitment"])
async def update_candidate(candidate_id: str, update_data: Dict[str, Any]):
    """Update candidate details (notes, status, etc.)."""
    try:
        await MongoDB.update_candidate(candidate_id, update_data)
        return {"status": "success", "message": "Candidate updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Payroll ──────────────────────────────────────────────────────────────────

@app.get("/payroll/{employee_id}", tags=["Payroll"])
async def get_payroll_records(employee_id: str):
    """Get payroll records for an employee."""
    db = get_sql_db()
    records = db.get_payroll_records(employee_id)
    return {"employee_id": employee_id, "records": records}


# ─── Stats ────────────────────────────────────────────────────────────────────

@app.get("/stats", tags=["Dashboard"])
async def get_dashboard_stats():
    """Get platform-wide statistics for the dashboard."""
    try:
        candidates = await MongoDB.list_candidates(limit=1000)
        total = len(candidates)
        shortlisted = sum(1 for c in candidates if c.get("status") == "shortlisted")
        hired = sum(1 for c in candidates if c.get("status") == "hired")
        avg_score = (
            sum(c.get("score", {}).get("total_score", 0) for c in candidates) / total
            if total > 0 else 0
        )

        db = get_sql_db()
        employees = db.list_employees()
        total_employees = len(employees)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        total = shortlisted = hired = total_employees = 0
        avg_score = 0.0

    return {
        "candidates": {
            "total": total,
            "shortlisted": shortlisted,
            "hired": hired,
            "average_score": round(avg_score, 1),
        },
        "employees": {
            "total": total_employees,
        },
        "platform": {
            "version": settings.APP_VERSION,
            "agents": ["cv_agent", "interview_agent", "onboarding_agent",
                       "training_agent", "payroll_agent", "leave_agent"],
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "backend.gateway.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
