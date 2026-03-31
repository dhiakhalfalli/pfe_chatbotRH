"""
CV Agent: Orchestrates the full CV processing pipeline.
Responsibilities: OCR, parsing, scoring, GitHub analysis.
"""
import logging
import uuid
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

from backend.services.ocr_service import ocr_service
from backend.services.cv_parser import cv_parser
from backend.tools.github_tool import github_tool
from backend.database.mongo import MongoDB
from backend.services.ats_service import ats_service


class CVAgent:
    """
    End-to-end CV processing agent.

    Pipeline:
    1. OCR text extraction
    2. Structured parsing (entities, skills, experience)
    3. Candidate scoring
    4. GitHub profile analysis
    5. Store in MongoDB
    """

    # Scoring weights
    SCORE_WEIGHTS = {
        "skills": 0.35,
        "experience": 0.30,
        "education": 0.20,
        "github": 0.10,
        "communication": 0.05,
    }

    async def process_cv(
        self,
        file_path: str,
        original_filename: str,
        file_size: int,
        job_title: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Full CV processing pipeline.
        Returns structured candidate profile with score.
        """
        logger.info(f"Starting CV processing: {original_filename}")
        result: Dict[str, Any] = {
            "status": "processing",
            "filename": original_filename,
            "pipeline_steps": [],
        }

        # ── Step 1: OCR ─────────────────────────────────────────────────────
        try:
            raw_text, ocr_confidence = ocr_service.extract_text(file_path)
            result["pipeline_steps"].append({"step": "ocr", "status": "success"})
            logger.info(f"OCR complete. Confidence: {ocr_confidence:.2f}, chars: {len(raw_text)}")
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raw_text = ""
            ocr_confidence = 0.0
            result["pipeline_steps"].append({"step": "ocr", "status": "failed", "error": str(e)})

        if not raw_text.strip():
            result["status"] = "failed"
            result["error"] = "Could not extract text from CV"
            return result

        # ── Step 2: Parse ────────────────────────────────────────────────────
        try:
            parsed = cv_parser.parse(raw_text, original_filename)
            result["pipeline_steps"].append({"step": "parse", "status": "success"})
            logger.info(f"CV parsed. Name: {parsed.get('full_name')}, Skills: {len(parsed.get('skills', []))}")
        except Exception as e:
            logger.error(f"CV parsing failed: {e}")
            parsed = {"raw_text": raw_text}
            result["pipeline_steps"].append({"step": "parse", "status": "failed", "error": str(e)})

        # ── Step 3: GitHub Analysis ──────────────────────────────────────────
        github_data = None
        if parsed.get("github_url"):
            try:
                github_data = github_tool.fetch_profile(parsed["github_url"])
                result["pipeline_steps"].append({"step": "github", "status": "success"})
            except Exception as e:
                logger.warning(f"GitHub analysis failed: {e}")
                result["pipeline_steps"].append({"step": "github", "status": "skipped"})

        # ── Step 4: Score ────────────────────────────────────────────────────
        score = self._score_candidate(parsed, github_data, required_skills)
        result["pipeline_steps"].append({"step": "scoring", "status": "success"})

        # ── Step 5: Build Profile ────────────────────────────────────────────
        candidate_id = str(uuid.uuid4())
        candidate_profile = {
            "id": candidate_id,
            "full_name": parsed.get("full_name") or self._guess_name(original_filename),
            "email": parsed.get("email"),
            "phone": parsed.get("phone"),
            "location": parsed.get("location"),
            "linkedin_url": parsed.get("linkedin_url"),
            "github_url": parsed.get("github_url"),
            "portfolio_url": parsed.get("portfolio_url"),
            "job_title_applied": job_title,
            "years_experience": parsed.get("years_experience"),
            "skills": parsed.get("skills", []),
            "education": parsed.get("education", []),
            "experience": parsed.get("experience", []),
            "certifications": parsed.get("certifications", []),
            "languages": parsed.get("languages", []),
            "summary": parsed.get("summary"),
            "raw_text": raw_text[:5000],  # Truncate for storage
            "cv_file_path": file_path,
            "github_profile": github_data,
            "score": score,
            "status": "pending",
            "cv_document": {
                "id": str(uuid.uuid4()),
                "candidate_id": candidate_id,
                "original_filename": original_filename,
                "file_path": file_path,
                "file_size_bytes": file_size,
                "ocr_confidence": ocr_confidence,
                "ocr_text": raw_text[:2000],
            },
        }

        # ── Step 6: ATS Integration ───────────────────────────────────────────
        try:
            # Send candidate to ATS (local or external)
            ats_candidate_id = await ats_service.create_candidate(candidate_profile)
            candidate_profile["ats_candidate_id"] = ats_candidate_id
            result["pipeline_steps"].append({"step": "ats_store", "status": "success"})
        except Exception as e:
            logger.error(f"ATS store failed: {e}")
            result["pipeline_steps"].append({"step": "ats_store", "status": "failed", "error": str(e)})

        result["status"] = "completed"
        result["candidate_id"] = candidate_id
        result["candidate"] = candidate_profile
        result["score"] = score

        logger.info(f"CV processing complete. Score: {score.get('total_score', 0):.1f}/100")
        return result

    async def process_cv_from_bytes(
        self,
        content: bytes,
        original_filename: str,
        mime_type: str,
        job_title: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Process CV from raw bytes (for API uploads)."""
        import tempfile
        import os

        suffix = ".pdf" if mime_type == "application/pdf" else ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = await self.process_cv(
                tmp_path, original_filename, len(content),
                job_title, required_skills
            )
        finally:
            os.unlink(tmp_path)

        return result

    def _score_candidate(
        self,
        parsed: Dict[str, Any],
        github_data: Optional[Dict[str, Any]],
        required_skills: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Compute multi-dimensional candidate score (0–100)."""
        scores: Dict[str, float] = {}
        notes: List[str] = []

        # Skills score
        skills = [s["name"].lower() if isinstance(s, dict) else s.lower()
                  for s in parsed.get("skills", [])]
        if required_skills:
            req_lower = [r.lower() for r in required_skills]
            matched = sum(1 for r in req_lower if any(r in s for s in skills))
            skills_score = min(100, (matched / max(len(req_lower), 1)) * 100)
            notes.append(f"Matched {matched}/{len(required_skills)} required skills")
        else:
            # General skill breadth score
            skills_score = min(100, len(skills) * 5)
            notes.append(f"Found {len(skills)} technical skills")
        scores["skills_score"] = round(skills_score, 2)

        # Experience score
        experiences = parsed.get("experience", [])
        years_exp = parsed.get("years_experience") or 0
        exp_score = min(100, years_exp * 10)  # 10 points/year, max 100
        if years_exp == 0 and experiences:
            exp_score = len(experiences) * 20  # Bonus for listed positions
        scores["experience_score"] = round(min(100, exp_score), 2)
        notes.append(f"~{years_exp} years experience detected")

        # Education score
        education = parsed.get("education", [])
        edu_score = 0
        for edu in education:
            degree = (edu.get("degree") or "").lower()
            if any(d in degree for d in ["phd", "doctorate"]):
                edu_score = 100
            elif any(d in degree for d in ["master", "msc", "mba"]):
                edu_score = max(edu_score, 85)
            elif any(d in degree for d in ["bachelor", "bsc", "licence", "ingénieur"]):
                edu_score = max(edu_score, 70)
            else:
                edu_score = max(edu_score, 50)
        scores["education_score"] = round(edu_score, 2)

        # GitHub score
        gh_score = 0
        if github_data:
            gh_score = github_data.get("contribution_score", 0)
            notes.append(f"GitHub: {github_data.get('username')} – score {gh_score:.1f}")
        scores["github_score"] = round(gh_score, 2)

        # Communication score (based on summary quality and languages)
        langs = parsed.get("languages", [])
        comm_score = 50  # Base
        if langs:
            comm_score += min(30, len(langs) * 10)
        if parsed.get("summary"):
            comm_score += 20
        scores["communication_score"] = round(min(100, comm_score), 2)

        # Weighted total
        total = (
            scores["skills_score"] * self.SCORE_WEIGHTS["skills"] +
            scores["experience_score"] * self.SCORE_WEIGHTS["experience"] +
            scores["education_score"] * self.SCORE_WEIGHTS["education"] +
            scores["github_score"] * self.SCORE_WEIGHTS["github"] +
            scores["communication_score"] * self.SCORE_WEIGHTS["communication"]
        )

        return {
            "total_score": round(total, 2),
            "skills_score": scores["skills_score"],
            "experience_score": scores["experience_score"],
            "education_score": scores["education_score"],
            "github_score": scores["github_score"],
            "communication_score": scores["communication_score"],
            "scoring_notes": notes,
        }

    @staticmethod
    def _guess_name(filename: str) -> str:
        """Derive candidate name from filename as fallback."""
        import re
        base = filename.replace(".pdf", "").replace(".docx", "")
        base = re.sub(r'[_\-\.]+', ' ', base)
        # Remove common words
        stop = {"cv", "resume", "fr", "en", "an", "last", "final", "new"}
        words = [w for w in base.split() if w.lower() not in stop]
        return " ".join(words[:3]).title() if words else "Unknown Candidate"


# Module singleton
cv_agent = CVAgent()
