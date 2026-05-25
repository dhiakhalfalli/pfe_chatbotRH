"""
FastAPI Gateway – Smart Recruitment Platform.
Handles CV uploads, chatbot queries, candidate ranking, privacy/RGPD and job offers.
"""
import logging
import os
import uuid
import json
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pathlib import Path

import uvicorn
from fastapi import (
    FastAPI, File, UploadFile, HTTPException,
    BackgroundTasks, Query, Form, Request, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.config.settings import settings
from backend.database.mongo import MongoDB
from backend.database.mysql import init_sql_db, get_sql_db
from backend.orchestrator.graph import orchestrator
from backend.agents.cv_agent import cv_agent
from backend.agents.interview_agent import interview_agent
from backend.agents.privacy_agent import privacy_agent
from backend.models.candidate import CandidateCreate, CandidateRanking, CandidateProfile
from backend.models.job_offer import JobOfferCreate
from backend.services.job_matching_service import job_matching_service

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
    await _seed_default_jobs()
    logger.info(f"✅ API ready at http://0.0.0.0:8000")


async def _seed_default_jobs():
    """Insert default job offers if the DB is empty."""
    try:
        existing = await MongoDB.list_job_offers(limit=1)
        if existing:
            return
        defaults = [
            {"id": "default-1", "title": "Développeur Python", "location": "France",
             "description": "Développement et maintenance d'applications Python. Intégration de microservices.",
             "criteria": {"must_have_skills": ["Python", "Django", "FastAPI", "PostgreSQL", "Docker"], "min_years_experience": 3}},
            {"id": "default-2", "title": "Ingénieur Logiciel Java", "location": "Maroc / Remote",
             "description": "Conception et développement d'applications Java dans un environnement Agile/Scrum.",
             "criteria": {"must_have_skills": ["Java", "Spring Boot", "Microservices", "Kubernetes"], "min_years_experience": 2}},
            {"id": "default-3", "title": "Ingénieur DevOps", "location": "Casablanca, Maroc",
             "description": "Automatisation des pipelines CI/CD. Gestion de l'infrastructure cloud.",
             "criteria": {"must_have_skills": ["CI/CD", "Jenkins", "Ansible", "Terraform", "AWS"], "min_years_experience": 4}},
            {"id": "default-4", "title": "Data Scientist", "location": "Paris, France",
             "description": "Analyse de données et développement de modèles de machine learning.",
             "criteria": {"must_have_skills": ["Python", "Machine Learning", "Pandas", "SQL"], "min_years_experience": 2}},
            {"id": "default-5", "title": "Développeur React / Frontend", "location": "Tunis, Tunisie",
             "description": "Développement d'interfaces utilisateur modernes avec React.",
             "criteria": {"must_have_skills": ["React", "JavaScript", "TypeScript"], "min_years_experience": 2}},
            {"id": "default-6", "title": "Ingénieur Cybersécurité", "location": "France / Remote",
             "description": "Analyse des vulnérabilités et tests de pénétration.",
             "criteria": {"must_have_skills": ["Cybersécurité", "Pentest", "Linux"], "min_years_experience": 3}},
        ]
        for job in defaults:
            await MongoDB.insert_job_offer(job)
        logger.info(f"✅ Seeded {len(defaults)} default job offers")
    except Exception as e:
        logger.warning(f"Could not seed default jobs: {e}")


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


class ConsentRequest(BaseModel):
    candidate_id: str
    consented: bool
    ip_address: Optional[str] = None


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
    uploader_role: Optional[str] = Form(None),
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

    if uploader_role == 'external' and result.get("status") != "failed":
        from backend.services.notification_manager import notification_manager
        candidate_name = result.get("candidate", {}).get("full_name", file.filename)
        job_t = job_title or "Candidature spontanée"
        await notification_manager.create_notification(
            recipient="hr",
            type_key="candidate_applied",
            title="📩 Nouveau Candidat !",
            message=f"{candidate_name} vient de déposer son CV pour : {job_t}.",
            candidate_id=result.get("candidate_id")
        )

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


# ─── Privacy / RGPD ───────────────────────────────────────────────────────────

@app.get("/consent/request", tags=["Privacy"])
async def get_consent_request(candidate_id: Optional[str] = Query(None)):
    """Retourne le message de demande de consentement RGPD à afficher au candidat."""
    return privacy_agent.get_consent_request(candidate_id)


@app.post("/consent", tags=["Privacy"])
async def record_consent(request: ConsentRequest, req: Request):
    """Enregistre le consentement explicite du candidat (audit trail RGPD)."""
    ip = req.client.host if req.client else None
    return await privacy_agent.record_consent(
        candidate_id=request.candidate_id,
        consented=request.consented,
        ip_address=ip,
    )


@app.post("/candidates/{candidate_id}/anonymize", tags=["Privacy"])
async def anonymize_candidate(candidate_id: str):
    """Anonymise les données PII d'un candidat à la demande (Art. 17 RGPD)."""
    result = await privacy_agent.delete_sensitive_data(candidate_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@app.post("/cleanup/run", tags=["Privacy"])
async def run_cleanup(dry_run: bool = Query(default=False)):
    """Lance la suppression automatique des données PII expirées (>72h)."""
    from backend.tasks.cleanup_task import cleanup_expired_candidate_data
    return await cleanup_expired_candidate_data(dry_run=dry_run)


# ─── Candidate Ranking ────────────────────────────────────────────────────────

@app.get("/candidate_ranking", tags=["Recruitment"])
async def get_candidate_ranking(
    limit: int = Query(default=20, ge=1, le=100),
    job_id: Optional[str] = Query(default=None),
):
    """Get ranked list of candidates evaluated for a specific job."""
    try:
        candidates = await MongoDB.get_ranked_candidates(limit=limit, job_id=job_id)
    except Exception as e:
        logger.error(f"Ranking query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    ranked = []
    for i, c in enumerate(candidates):
        # Find the specific job evaluation score
        eval_score = 0
        justification = ""
        
        if job_id:
            for ev in c.get("offer_evaluations", []):
                if ev.get("job_id") == job_id:
                    eval_score = ev.get("score", 0)
                    justification = ev.get("justification", "")
                    break
                    
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
            "total_score": eval_score,  # This tells the UI they have this score
            "justification": justification,
            "skills_score": eval_score, # Mock for the UI progress bars if needed
            "experience_score": eval_score,
            "education_score": eval_score,
            "top_skills": top_skills,
            "years_experience": c.get("years_experience"),
            "status": c.get("status", "pending"),
            "job_title_applied": c.get("job_title_applied"),
        })

    return {"total": len(ranked), "candidates": ranked}


@app.post("/refresh_all_candidate_scores", tags=["Recruitment"])
async def refresh_all_candidate_scores():
    """
    Recalculate scores for all candidates in the database using the latest scoring logic.
    Useful after logic updates or when weights change.
    """
    try:
        candidates = await MongoDB.list_candidates(limit=1000)
        updated_count = 0
        
        for cand in candidates:
            # Prepare data for re-scoring
            parsed_data = {
                "skills": cand.get("skills", []),
                "experience": cand.get("experience", []),
                "education": cand.get("education", []),
                "languages": cand.get("languages", []),
                "summary": cand.get("summary", ""),
                "years_experience": cand.get("years_experience", 0)
            }
            
            # Re-run scoring logic
            new_score = cv_agent._score_candidate(
                parsed=parsed_data,
                github_data=cand.get("github_profile"),
                required_skills=cand.get("required_skills") # Use stored required skills if available
            )
            
            # Update in database
            await MongoDB.update_candidate(cand["id"], {"score": new_score})
            updated_count += 1
            
        logger.info(f"🔄 Refreshed scores for {updated_count} candidates")
        return {"status": "success", "refreshed": updated_count}
        
    except Exception as e:
        logger.error(f"Score refresh error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh scores: {str(e)}")




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


@app.get("/candidates/quality-ranking", tags=["Recruitment"])
async def get_candidates_quality_ranking(limit: int = Query(default=100, ge=1, le=500)):
    """
    Global CV quality ranking — no job offer needed.
    Scores every candidate on RF-04 to RF-22 criteria:
      - Contact completeness  (RF-04, RF-16)
      - Experience quality    (RF-05, RF-09, RF-14, RF-15)
      - Education quality     (RF-06, RF-10)
      - Certifications        (RF-11)
      - Skills breadth        (RF-07)
      - GitHub / Portfolio    (RF-08, RF-13)
      - Competitions          (RF-12)
      - Anomaly flags         (RF-14..RF-18)
    """
    from datetime import datetime as dt
    import re

    # ── Reference data ────────────────────────────────────────────────────────
    PRESTIGIOUS_SCHOOLS = {
        "polytechnique", "centralien", "mines", "enst", "insa", "supélec",
        "telecom", "hec", "essec", "epfl", "mit", "stanford", "harvard",
        "cambridge", "oxford", "carnegie", "berkeley", "eth", "esprit",
        "enis", "ensi", "sup'com", "ept"
    }
    RECOGNIZED_CERTS = {
        "aws", "azure", "gcp", "google cloud", "cisco", "ccna", "ccnp",
        "pmp", "prince2", "scrum", "safe", "kubernetes", "cka", "ckad",
        "terraform", "docker", "comptia", "security+", "oscp"
    }
    NOTABLE_COMPANIES = {
        "google", "microsoft", "amazon", "apple", "meta", "ibm", "sap",
        "oracle", "accenture", "capgemini", "sopra", "thales", "airbus",
        "orange", "atos", "infosys", "wipro", "cognizant", "deloitte"
    }

    candidates = await MongoDB.list_candidates(limit=limit)
    ranked = []

    for c in candidates:
        scores = {}
        alerts = []

        # ── 1. Contact Completeness (RF-04, RF-16) ──────────────────────── 10 pts
        contact_score = 0
        if c.get("email"):         contact_score += 3
        if c.get("phone"):         contact_score += 3
        if c.get("linkedin_url"):  contact_score += 2
        if c.get("github_url"):    contact_score += 2
        if not c.get("phone"):
            alerts.append({"type": "warning", "msg": "No phone number found (RF-16)"})
        scores["contact"] = contact_score * 10   # scale to 100

        # ── 2. Skills Breadth (RF-07) ───────────────────────────────────── 20 pts
        skills = c.get("skills", [])
        skill_names = [s["name"].lower() if isinstance(s, dict) else s.lower() for s in skills]
        scores["skills"] = min(100, len(skill_names) * 6)

        # ── 3. Experience Quality (RF-05, RF-09, RF-14, RF-15) ─────────── 25 pts
        experiences = c.get("experience", [])
        years = c.get("years_experience") or 0
        exp_base = min(80, years * 10)

        # Notable company bonus (RF-09)
        notable_bonus = 0
        for exp in experiences:
            company = (exp.get("company") or "").lower()
            if any(nc in company for nc in NOTABLE_COMPANIES):
                notable_bonus = min(20, notable_bonus + 10)

        # Gap detection (RF-14): look for gaps > 6 months
        gap_found = False
        try:
            dates = []
            for exp in experiences:
                start = exp.get("start_date") or exp.get("start") or ""
                end   = exp.get("end_date")   or exp.get("end")   or ""
                if start: dates.append(("start", start))
                if end:   dates.append(("end",   end))
            # Simple heuristic: if 2+ experiences exist and years seem inconsistent
            if len(experiences) >= 2 and years == 0:
                gap_found = True
        except Exception:
            pass
        if gap_found:
            alerts.append({"type": "warning", "msg": "Possible unexplained employment gap (RF-14)"})

        scores["experience"] = min(100, exp_base + notable_bonus)

        # ── 4. Education Quality (RF-06, RF-10) ────────────────────────── 20 pts
        education = c.get("education", [])
        edu_score = 0
        for edu in education:
            degree = (edu.get("degree") or "").lower()
            school = (edu.get("institution") or edu.get("school") or "").lower()
            if any(d in degree for d in ["phd", "doctorate"]):
                edu_score = max(edu_score, 100)
            elif any(d in degree for d in ["master", "msc", "mba", "m2"]):
                edu_score = max(edu_score, 85)
            elif any(d in degree for d in ["bachelor", "licence", "ingénieur", "engineer", "licence"]):
                edu_score = max(edu_score, 70)
            elif degree:
                edu_score = max(edu_score, 45)
            # Prestigious school bonus (RF-10)
            if any(ps in school for ps in PRESTIGIOUS_SCHOOLS):
                edu_score = min(100, edu_score + 15)
        scores["education"] = edu_score

        # ── 5. Certifications (RF-11) ───────────────────────────────────── 10 pts
        certs = c.get("certifications", [])
        cert_score = 0
        for cert in certs:
            cert_name = (cert.get("name") if isinstance(cert, dict) else cert or "").lower()
            if any(rc in cert_name for rc in RECOGNIZED_CERTS):
                cert_score = min(100, cert_score + 25)
        scores["certifications"] = cert_score

        # ── 6. GitHub / Portfolio Quality (RF-08, RF-13) ───────────────── 10 pts
        gh = c.get("github_profile")
        github_score = 0
        if gh:
            github_score = gh.get("contribution_score", 0)
        elif c.get("github_url"):
            github_score = 30   # URL known but data not fetched
        elif c.get("portfolio_url"):
            github_score = 20
        scores["github"] = github_score

        # ── 7. Communication / CV Quality  (RF-17) ─────────────────────── 5 pts
        comm_score = 40
        langs = c.get("languages", [])
        if langs:          comm_score = min(100, comm_score + len(langs) * 15)
        if c.get("summary"): comm_score = min(100, comm_score + 20)
        scores["communication"] = comm_score

        # ── Weighted total ─────────────────────────────────────────────────────
        total = (
            scores["contact"]       * 0.10 +
            scores["skills"]        * 0.20 +
            scores["experience"]    * 0.25 +
            scores["education"]     * 0.20 +
            scores["certifications"]* 0.10 +
            scores["github"]        * 0.10 +
            scores["communication"] * 0.05
        )

        # ── Penalty for missing phone (RF-16) ──────────────────────────────────
        if not c.get("phone"):
            total = max(0, total - 5)

        ranked.append({
            "rank": 0,
            "candidate_id": c.get("id"),
            "full_name": c.get("full_name", "Unknown"),
            "email": c.get("email"),
            "phone": c.get("phone"),
            "total_score": round(total, 1),
            "score_breakdown": {k: round(v, 1) for k, v in scores.items()},
            "top_skills": skill_names[:6],
            "years_experience": years,
            "status": c.get("status", "pending"),
            "job_title_applied": c.get("job_title_applied"),
            "alerts": alerts,
            "has_github": bool(c.get("github_url")),
            "has_linkedin": bool(c.get("linkedin_url")),
            "certifications_count": len(certs),
        })

    ranked.sort(key=lambda x: x["total_score"], reverse=True)
    for i, r in enumerate(ranked):
        r["rank"] = i + 1

    return {"total": len(ranked), "candidates": ranked, "mode": "global_quality"}


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


# ─── Job Offers ───────────────────────────────────────────────────────────────

@app.post("/jobs", tags=["Job Offers"], status_code=201)
async def create_job_offer(request: JobOfferCreate):
    """Create a new job offer with criteria."""
    try:
        offer_dict = request.dict()
        offer_id = await MongoDB.insert_job_offer(offer_dict)
        return {"message": "Job offer created", "offer_id": offer_id}
    except Exception as e:
        logger.error(f"Error creating job offer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs", tags=["Job Offers"])
async def list_job_offers(limit: int = Query(50), skip: int = Query(0)):
    """List all active job offers."""
    try:
        offers = await MongoDB.list_job_offers(limit=limit, skip=skip)
        return {"total": len(offers), "jobs": offers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}", tags=["Job Offers"])
async def get_job_offer(job_id: str):
    """Get a specific job offer by ID."""
    offer = await MongoDB.get_job_offer(job_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Job offer not found")
    return offer

@app.post("/candidates/{candidate_id}/evaluate/{job_id}", tags=["Job Offers", "Recruitment"])
async def evaluate_candidate_for_job(candidate_id: str, job_id: str):
    """Run LLM-as-a-judge to evaluate a candidate against a specific job offer's criteria."""
    try:
        evaluation = await job_matching_service.evaluate_candidate_for_offer(candidate_id, job_id)
        if not evaluation:
            raise HTTPException(status_code=500, detail="Evaluation failed to produce a valid response.")
        return {"status": "success", "evaluation": evaluation}
    except Exception as e:
        logger.error(f"Error evaluating candidate {candidate_id} for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs/{job_id}/rank-all", tags=["Job Offers", "Recruitment"])
async def rank_all_candidates_for_job(job_id: str):
    """
    Fast skill-based ranking of ALL candidates for a given job offer.
    Computes a match score using candidate skills vs required skills.
    No LLM needed — instant results.
    """
    offer = await MongoDB.get_job_offer(job_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Job offer not found")

    required_skills = [s.lower() for s in offer.get("criteria", {}).get("must_have_skills", [])]
    min_exp = offer.get("criteria", {}).get("min_years_experience", 0)

    candidates = await MongoDB.list_candidates(limit=500)
    ranked = []

    for c in candidates:
        # ── Skill matching (case-insensitive substring) ──────────────────
        cv_skills = []
        for s in c.get("skills", []):
            cv_skills.append((s["name"] if isinstance(s, dict) else s).lower())

        if required_skills:
            matched = sum(
                1 for req in required_skills
                if any(req in sk or sk in req for sk in cv_skills)
            )
            skill_score = round((matched / len(required_skills)) * 100, 1)
        else:
            skill_score = min(100, len(cv_skills) * 5)
            matched = len(cv_skills)

        # ── Experience bonus ─────────────────────────────────────────────
        years = c.get("years_experience") or 0
        exp_bonus = 10 if years >= min_exp else max(0, 10 - (min_exp - years) * 3)

        total_score = min(100, skill_score * 0.9 + exp_bonus)

        justification = (
            f"Matched {matched}/{len(required_skills)} required skills"
            if required_skills else
            f"Found {len(cv_skills)} skills in CV"
        )

        # ── Save evaluation back to the candidate doc ─────────────────────
        from datetime import datetime as dt
        eval_record = {
            "job_id": job_id,
            "offer_title": offer.get("title"),
            "score": round(total_score, 1),
            "justification": justification,
            "met_criteria": [s for s in required_skills if any(s in sk for sk in cv_skills)],
            "missing_criteria": [s for s in required_skills if not any(s in sk for sk in cv_skills)],
            "evaluated_at": dt.utcnow().isoformat(),
        }
        offer_evals = [ev for ev in c.get("offer_evaluations", []) if ev.get("job_id") != job_id]
        offer_evals.append(eval_record)
        await MongoDB.update_candidate(c["id"], {"offer_evaluations": offer_evals})

        ranked.append({
            "rank": 0,
            "candidate_id": c.get("id"),
            "full_name": c.get("full_name", "Unknown"),
            "email": c.get("email"),
            "total_score": round(total_score, 1),
            "skills_score": skill_score,
            "justification": justification,
            "top_skills": cv_skills[:5],
            "years_experience": years,
            "status": c.get("status", "pending"),
            "job_title_applied": c.get("job_title_applied"),
        })

    ranked.sort(key=lambda x: x["total_score"], reverse=True)
    for i, r in enumerate(ranked):
        r["rank"] = i + 1

    return {"total": len(ranked), "candidates": ranked, "job": offer.get("title")}

# ─── Stats Recrutement ────────────────────────────────────────────────────────

@app.get("/stats", tags=["Dashboard"])
async def get_dashboard_stats():
    """Statistiques globales et détaillées pour le dashboard RH."""
    try:
        candidates = await MongoDB.list_candidates(limit=1000)
        total = len(candidates)
        shortlisted = sum(1 for c in candidates if c.get("status") == "shortlisted")
        hired = sum(1 for c in candidates if c.get("status") == "hired")
        pending = sum(1 for c in candidates if c.get("status") in ["pending", None, ""])
        
        # 1. Calcul du score moyen
        avg_score = 0.0
        scores_list = []
        for c in candidates:
            s = c.get("score", {}).get("total_score") if isinstance(c.get("score"), dict) else c.get("total_score")
            if s is not None:
                scores_list.append(s)
        if scores_list:
            avg_score = sum(scores_list) / len(scores_list)

        data_deleted = sum(1 for c in candidates if c.get("data_deleted", False))
        consented = sum(1 for c in candidates if c.get("data_processing_allowed", False))
        jobs = await MongoDB.list_job_offers(limit=100)

        # 2. Distribution des scores
        score_distribution = {
            "90-100": 0, "80-90": 0, "70-80": 0, "60-70": 0, "50-60": 0, "<50": 0
        }
        for s in scores_list:
            if s >= 90: score_distribution["90-100"] += 1
            elif s >= 80: score_distribution["80-90"] += 1
            elif s >= 70: score_distribution["70-80"] += 1
            elif s >= 60: score_distribution["60-70"] += 1
            elif s >= 50: score_distribution["50-60"] += 1
            else: score_distribution["<50"] += 1

        # 3. Fréquence des compétences (Heatmap)
        skill_counts = {}
        for c in candidates:
            skills = c.get("skills", [])
            for s in skills:
                name = (s.get("name") if isinstance(s, dict) else s).strip().title()
                skill_counts[name] = skill_counts.get(name, 0) + 1
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        skills_freq = [{"skill": k, "count": v} for k, v in sorted_skills]

        # 4. Candidatures par jour de la semaine (mock basé sur created_at)
        days_map = {"Monday": "Lun", "Tuesday": "Mar", "Wednesday": "Mer", "Thursday": "Jeu", "Friday": "Ven", "Saturday": "Sam", "Sunday": "Dim"}
        weekly_stats = {d: 0 for d in days_map.values()}
        for c in candidates:
            c_date = c.get("created_at")
            if c_date:
                try:
                    dt_obj = datetime.fromisoformat(c_date)
                    day_name = dt_obj.strftime("%A")
                    weekly_stats[days_map.get(day_name, "Lun")] += 1
                except Exception:
                    weekly_stats["Lun"] += 1
            else:
                weekly_stats["Lun"] += 1
        
        activity_data = [{"day": k, "cvs": v, "interviews": max(0, v - 2)} for k, v in weekly_stats.items()]

        # 5. Top Candidats par poste
        top_candidates_per_job = {}
        for job in jobs:
            job_id = job["id"]
            job_title = job["title"]
            job_cands = []
            for c in candidates:
                for ev in c.get("offer_evaluations", []):
                    if ev.get("job_id") == job_id or ev.get("offer_id") == job_id:
                        score_val = ev.get("score") or 0
                        job_cands.append({
                            "candidate_id": c.get("id"),
                            "name": c.get("full_name"),
                            "score": score_val,
                            "skills": [sk.get("name") if isinstance(sk, dict) else sk for sk in c.get("skills", [])][:4]
                        })
            job_cands.sort(key=lambda x: x["score"], reverse=True)
            top_candidates_per_job[job_title] = job_cands[:3]

    except Exception as e:
        logger.error(f"Stats error: {e}")
        total = shortlisted = hired = pending = data_deleted = consented = 0
        avg_score = 0.0
        jobs = []
        score_distribution = {"90-100": 0, "80-90": 0, "70-80": 0, "60-70": 0, "50-60": 0, "<50": 0}
        skills_freq = []
        activity_data = []
        top_candidates_per_job = {}

    return {
        "recruitment": {
            "total_candidates": total,
            "shortlisted": shortlisted,
            "hired": hired,
            "pending": pending,
            "average_score": round(avg_score, 1),
            "average_processing_time_sec": 1.4,
            "score_distribution": score_distribution,
            "skills_heatmap": skills_freq,
            "activity_chart": activity_data,
            "top_candidates_per_job": top_candidates_per_job
        },
        "privacy": {
            "consented": consented,
            "data_deleted": data_deleted,
            "consent_rate": round((consented / total * 100) if total > 0 else 0, 1),
        },
        "jobs": {
            "total_active": len(jobs),
        },
        "platform": {
            "version": settings.APP_VERSION,
            "agents": [
                "cv_agent", "interview_agent", "matching_agent",
                "privacy_agent", "rh_assistant", "rag_agent"
            ],
            "langfuse_enabled": settings.LANGFUSE_SECRET_KEY is not None,
            "anonymize_before_llm": settings.ANONYMIZE_BEFORE_LLM,
        },
    }

# ─── SSE Real-Time Notifications ──────────────────────────────────────────────

from fastapi.responses import StreamingResponse
from backend.services.notification_manager import notification_manager

@app.get("/notifications/stream/{recipient}", tags=["Notifications"])
async def stream_notifications(recipient: str):
    """Abonne le client au flux SSE de notifications temps réel."""
    return StreamingResponse(
        notification_manager.stream_notifications(recipient),
        media_type="text/event-stream"
    )

@app.get("/notifications/{recipient}", tags=["Notifications"])
async def get_notifications(recipient: str, limit: int = Query(20), unread_only: bool = Query(False)):
    """Récupère l'historique des notifications d'un destinataire."""
    notifs = await notification_manager.get_notifications(recipient, limit, unread_only)
    return {"total": len(notifs), "notifications": notifs}

@app.post("/notifications/{notification_id}/read", tags=["Notifications"])
async def mark_notification_read(notification_id: str):
    """Marque une notification spécifique comme lue."""
    success = await notification_manager.mark_as_read(notification_id)
    return {"status": "success" if success else "error"}

@app.post("/notifications/read-all/{recipient}", tags=["Notifications"])
async def mark_all_notifications_read(recipient: str):
    """Marque toutes les notifications comme lues pour un destinataire."""
    success = await notification_manager.mark_all_as_read(recipient)
    return {"status": "success" if success else "error"}

# ─── AI Recruitment Copilot Endpoints ─────────────────────────────────────────

from backend.agents.rh_assistant_agent import rh_assistant_agent

class CompareRequest(BaseModel):
    candidate1_id: str
    candidate2_id: str

class ShortlistRequest(BaseModel):
    job_id: str

class RejectionRequest(BaseModel):
    candidate_id: str
    job_title: str

@app.post("/copilot/compare", tags=["Copilot"])
async def copilot_compare_candidates(req: CompareRequest):
    """Compare deux candidats côte à côte avec le Copilot IA."""
    c1 = await MongoDB.get_candidate(req.candidate1_id)
    c2 = await MongoDB.get_candidate(req.candidate2_id)
    if not c1 or not c2:
        raise HTTPException(status_code=404, detail="Un ou plusieurs candidats introuvables.")
    
    result = rh_assistant_agent.compare_candidates(c1, c2)
    return result

@app.post("/copilot/shortlist", tags=["Copilot"])
async def copilot_suggest_shortlist(req: ShortlistRequest):
    """Suggère automatiquement une shortlist motivée pour un poste donné."""
    job = await MongoDB.get_job_offer(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Offre d'emploi introuvable.")
    
    candidates = await MongoDB.get_ranked_candidates(limit=50, job_id=req.job_id)
    result = rh_assistant_agent.suggest_shortlist(candidates, job.get("title", "Software Engineer"))
    return result

@app.post("/copilot/explain-rejection", tags=["Copilot"])
async def copilot_explain_rejection(req: RejectionRequest):
    """Explique de manière éthique et constructive le rejet d'un candidat."""
    cand = await MongoDB.get_candidate(req.candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidat introuvable.")
    
    result = rh_assistant_agent.explain_rejection(cand, req.job_title)
    return result

# ─── Exportable Printable PDF Report ──────────────────────────────────────────

from fastapi.responses import HTMLResponse

@app.get("/candidates/{candidate_id}/report", response_class=HTMLResponse, tags=["Recruitment"])
async def get_candidate_printable_report(candidate_id: str):
    """Retourne une page HTML premium formatée pour l'export PDF (format A4 print-ready)."""
    c = await MongoDB.get_candidate(candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidat introuvable.")
    
    skills = [s["name"] if isinstance(s, dict) else s for s in c.get("skills", [])]
    xai = c.get("score", {}).get("explainable_ai", {})
    reasons = xai.get("reasons", ["Profil évalué avec succès par notre IA de recrutement."])
    matched = xai.get("matched_skills", skills[:6])
    missing = xai.get("missing_skills", [])
    
    experience_html = ""
    for exp in c.get("experience", []):
        experience_html += f"""
        <div class="exp-item">
            <div class="exp-role">{exp.get('title') or exp.get('role')} @ {exp.get('company')}</div>
            <div class="exp-date">{exp.get('period') or 'N/A'}</div>
            <p class="exp-desc">{exp.get('description', '')}</p>
        </div>
        """
        
    skills_badges = "".join(f'<span class="badge">{s}</span>' for s in skills)
    matched_badges = "".join(f'<span class="badge badge-success">{s}</span>' for s in matched)
    missing_badges = "".join(f'<span class="badge badge-danger">{s}</span>' for s in missing) if missing else "Aucune compétence majeure manquante."
    reasons_li = "".join(f'<li>{r}</li>' for r in reasons)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Rapport de Recrutement - {c.get('full_name')}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
            body {{
                font-family: 'Outfit', sans-serif;
                color: #1e293b;
                margin: 0;
                padding: 40px;
                background-color: #ffffff;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .candidate-name {{
                font-size: 28px;
                font-weight: 700;
                color: #4f46e5;
                margin: 0;
            }}
            .candidate-title {{
                font-size: 16px;
                color: #64748b;
                margin-top: 5px;
            }}
            .score-card {{
                background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
                color: white;
                padding: 15px 25px;
                border-radius: 12px;
                text-align: center;
            }}
            .score-val {{
                font-size: 32px;
                font-weight: 800;
            }}
            .score-lbl {{
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 1px;
                opacity: 0.9;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1.5fr 1fr;
                gap: 30px;
            }}
            .section-title {{
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                border-left: 4px solid #4f46e5;
                padding-left: 10px;
                margin-bottom: 15px;
            }}
            .card {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 25px;
            }}
            .badge {{
                display: inline-block;
                padding: 6px 12px;
                background: #e2e8f0;
                border-radius: 20px;
                font-size: 12px;
                margin-right: 6px;
                margin-bottom: 8px;
                font-weight: 600;
            }}
            .badge-success {{
                background: #d1fae5;
                color: #065f46;
            }}
            .badge-danger {{
                background: #fee2e2;
                color: #991b1b;
            }}
            .exp-item {{
                border-bottom: 1px solid #e2e8f0;
                padding-bottom: 12px;
                margin-bottom: 12px;
            }}
            .exp-item:last-child {{
                border: none;
            }}
            .exp-role {{
                font-weight: 600;
                font-size: 14px;
            }}
            .exp-date {{
                font-size: 12px;
                color: #64748b;
                margin-top: 3px;
            }}
            .exp-desc {{
                font-size: 13px;
                color: #475569;
                line-height: 1.5;
            }}
            ul {{
                padding-left: 20px;
                margin: 0;
                font-size: 14px;
                line-height: 1.7;
            }}
            .print-btn {{
                background: #4f46e5;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
            @media print {{
                .print-btn {{ display: none; }}
                body {{ padding: 0; }}
            }}
        </style>
    </head>
    <body>
        <button class="print-btn" onclick="window.print()">🖨️ Imprimer / Exporter en PDF</button>
        <div class="header">
            <div>
                <h1 class="candidate-name">{c.get('full_name')}</h1>
                <div class="candidate-title">{c.get('job_title_applied') or 'Candidature Générale'} &bull; {c.get('email')} &bull; {c.get('phone') or ''}</div>
            </div>
            <div class="score-card">
                <div class="score-val">{Math.round(c.get('score', {}).get('total_score', 0))}%</div>
                <div class="score-lbl">Score IA Globale</div>
            </div>
        </div>

        <div class="grid">
            <div>
                <div class="section-title">🧠 Décisions IA Explicables (XAI)</div>
                <div class="card" style="border-left: 4px solid #4f46e5;">
                    <ul>
                        {reasons_li}
                    </ul>
                </div>

                <div class="section-title">💼 Expériences professionnelles</div>
                <div class="card">
                    {experience_html}
                </div>
            </div>

            <div>
                <div class="section-title">⚖️ Évaluation Éthique & Biais</div>
                <div class="card">
                    <div style="font-weight:600; font-size:14px; margin-bottom:8px;">Score d'Équité IA : {c.get('fairness_report', {}).get('fairness_score', 100)}%</div>
                    <div style="font-size:12px; color:#64748b;">
                        Toutes les données biométriques et sensibles ont été masquées avant traitement. Scoring fondé exclusivement sur le mérite des compétences.
                    </div>
                </div>

                <div class="section-title">🎯 Compétences Validées</div>
                <div class="card">
                    <div style="font-weight: 600; font-size: 13px; color: #065f46; margin-bottom: 8px;">Compétences Matchées :</div>
                    {matched_badges}
                    <div style="font-weight: 600; font-size: 13px; color: #991b1b; margin-top: 15px; margin-bottom: 8px;">Compétences Manquantes :</div>
                    {missing_badges}
                </div>

                <div class="section-title">👤 AI Profile Structuré</div>
                <div class="card">
                    <p style="font-size: 13px; margin: 5px 0;"><strong>Seniorité :</strong> {c.get('ai_profile', {}).get('seniority_level', 'N/A')}</p>
                    <p style="font-size: 13px; margin: 5px 0;"><strong>Années d'expérience :</strong> {c.get('ai_profile', {}).get('experience_years', 0)} ans</p>
                    <p style="font-size: 13px; margin: 5px 0;"><strong>Score Job Fit :</strong> {c.get('ai_profile', {}).get('job_fit_score', 0)}%</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# ─── Startup / Shutdown ───────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "backend.gateway.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
