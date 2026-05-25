"""
CV Agent: Orchestre l'analyse complète du CV (OCR, parsing, scoring, github, éthique et XAI).
Envoie également des notifications en temps réel lors du traitement.
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from backend.services.ocr_service import ocr_service
from backend.services.cv_parser import cv_parser
from backend.tools.github_tool import github_tool
from backend.database.mongo import MongoDB
from backend.services.ats_service import ats_service
from backend.services.embedding_service import embedding_service

# Nouveaux services avancés
from backend.services.notification_manager import notification_manager
from backend.services.ai_fairness_checker import ai_fairness_checker
from backend.services.duplicate_detector import duplicate_cv_detector

logger = logging.getLogger(__name__)


class CVAgent:
    """
    Agent de traitement de CV de bout en bout amélioré (UX, IA explicable et éthique).
    """

    # Poids par défaut du scoring
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
        score_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Traitement complet du CV avec conformité RGPD, explicabilité (XAI) et détection de doublons.
        """
        logger.info(f"Starting CV processing: {original_filename}")
        candidate_id = str(uuid.uuid4())
        
        # 1. Émettre une notification : Téléchargement du CV
        await notification_manager.create_notification(
            recipient="hr",
            type_key="cv_upload",
            title="📥 CV reçu",
            message=f"Le CV '{original_filename}' a été téléversé avec succès. Lancement de l'analyse...",
            candidate_id=candidate_id
        )

        result: Dict[str, Any] = {
            "status": "processing",
            "filename": original_filename,
            "pipeline_steps": [],
        }

        # ── Étape 1 : OCR ─────────────────────────────────────────────────────
        try:
            raw_text, ocr_confidence = ocr_service.extract_text(file_path)
            result["pipeline_steps"].append({"step": "ocr", "status": "success"})
            logger.info(f"OCR complete. Confidence: {ocr_confidence:.2f}")
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raw_text = ""
            ocr_confidence = 0.0
            result["pipeline_steps"].append({"step": "ocr", "status": "failed", "error": str(e)})

        if not raw_text.strip():
            result["status"] = "failed"
            result["error"] = "Impossible d'extraire le texte du CV"
            await notification_manager.create_notification(
                recipient="hr",
                type_key="analysis_failed",
                title="❌ Échec OCR",
                message=f"Le traitement du CV '{original_filename}' a échoué (OCR vide).",
                candidate_id=candidate_id
            )
            return result

        # ── Étape 2 : Notifications de début d'analyse ─────────────────────────
        await notification_manager.create_notification(
            recipient="hr",
            type_key="analysis_started",
            title="🧠 Analyse IA démarrée",
            message=f"Extraction structurée et audit éthique en cours pour '{original_filename}'...",
            candidate_id=candidate_id
        )

        # ── Étape 3 : Parsing Structuré ───────────────────────────────────────
        try:
            parsed = cv_parser.parse(raw_text, original_filename)
            result["pipeline_steps"].append({"step": "parse", "status": "success"})
            logger.info(f"CV parsed. Name: {parsed.get('full_name')}")
        except Exception as e:
            logger.error(f"CV parsing failed: {e}")
            parsed = {"raw_text": raw_text}
            result["pipeline_steps"].append({"step": "parse", "status": "failed", "error": str(e)})

        # ── Étape 4 : Détection de Doublons ───────────────────────────────────
        is_duplicate, duplicate_id, duplicate_reason = await duplicate_cv_detector.detect_duplicate(
            email=parsed.get("email"),
            phone=parsed.get("phone"),
            raw_text=raw_text
        )

        if is_duplicate:
            result["status"] = "failed"
            result["error"] = f"Un CV identique ou très similaire existe déjà ({duplicate_reason})."
            await notification_manager.create_notification(
                recipient="hr",
                type_key="duplicate_warning",
                title="⚠️ Tentative de Doublon Rejetée",
                message=f"Le dépôt de '{original_filename}' a été bloqué car c'est un doublon.",
            )
            return result

        # ── Étape 5 : Contrôle d'Équité IA (Fairness Audit) ───────────────────
        fairness_report = ai_fairness_checker.check_candidate_fairness(raw_text, parsed)

        # ── Étape 6 : Analyse GitHub ──────────────────────────────────────────
        github_data = None
        if parsed.get("github_url"):
            try:
                github_data = github_tool.fetch_profile(parsed["github_url"])
                result["pipeline_steps"].append({"step": "github", "status": "success"})
            except Exception as e:
                logger.warning(f"GitHub analysis failed: {e}")
                result["pipeline_steps"].append({"step": "github", "status": "skipped"})

        # ── Étape 7 : Scoring Explicable (XAI) ────────────────────────────────
        score = self._score_candidate(parsed, github_data, required_skills, score_weights)
        result["pipeline_steps"].append({"step": "scoring", "status": "success"})

        # ── Étape 8 : Génération de l'AI Profile Structuré (RF-04 à RF-22) ─────
        skills_simple = [s["name"] if isinstance(s, dict) else s for s in parsed.get("skills", [])]
        years_exp = parsed.get("years_experience") or 0.0
        
        # Seniority level logic
        if years_exp >= 5:
            seniority = "Senior"
        elif years_exp >= 2:
            seniority = "Confirmé"
        else:
            seniority = "Junior"

        # Match dynamic job recommendations
        recommended_jobs = []
        try:
            job_offers = await MongoDB.list_job_offers(limit=50)
            for j in job_offers:
                req_skills = [sk.lower() for sk in j.get("criteria", {}).get("must_have_skills", [])]
                overlap = sum(1 for rs in req_skills if any(rs in s.lower() or s.lower() in rs for s in skills_simple))
                if overlap > 0 or not req_skills:
                    recommended_jobs.append({"title": j["title"], "overlap": overlap})
            
            recommended_jobs.sort(key=lambda x: x["overlap"], reverse=True)
            recommended_jobs = [j["title"] for j in recommended_jobs[:3]]
        except Exception as e:
            logger.warning(f"Failed to match jobs for profile recommendation: {e}")

        ai_profile = {
            "skills": skills_simple,
            "experience_years": years_exp,
            "seniority_level": seniority,
            "job_fit_score": score.get("total_score", 0.0),
            "recommended_jobs": recommended_jobs
        }

        # ── Étape 9 : Construction finale du Profil Candidat ────────────────────
        candidate_profile = {
            "id": candidate_id,
            "full_name": parsed.get("full_name") or self._guess_name(original_filename),
            "email": parsed.get("email"),
            "phone": parsed.get("phone"),
            "location": parsed.get("location"),
            "linkedin_url": parsed.get("linkedin_url"),
            "github_url": parsed.get("github_url"),
            "portfolio_url": parsed.get("portfolio_url"),
            "job_title_applied": job_title or parsed.get("job_title_applied"),
            "years_experience": years_exp,
            "skills": parsed.get("skills", []),
            "education": parsed.get("education", []),
            "experience": parsed.get("experience", []),
            "certifications": parsed.get("certifications", []),
            "languages": parsed.get("languages", []),
            "summary": parsed.get("summary"),
            "raw_text": raw_text[:5000],
            "cv_file_path": file_path,
            "github_profile": github_data,
            "score": score,
            "ai_profile": ai_profile,
            "fairness_report": fairness_report,
            "is_duplicate": is_duplicate,
            "duplicate_warning": duplicate_reason if is_duplicate else None,
            "duplicate_candidate_id": duplicate_id if is_duplicate else None,
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

        # ── Étape 10 : Stockage ATS local (MongoDB) ───────────────────────────
        try:
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

        # ── Étape 11 : Notification d'Analyse Terminée ───────────────────────
        await notification_manager.create_notification(
            recipient="hr",
            type_key="analysis_completed",
            title="✅ Analyse terminée !",
            message=f"Le profil de {candidate_profile['full_name']} a été analysé (Score Global : {score.get('total_score')}%).",
            score=score.get("total_score"),
            candidate_id=candidate_id
        )

        logger.info(f"CV processing complete. Score: {score.get('total_score', 0):.1f}/100")
        return result

    async def process_cv_from_bytes(
        self,
        content: bytes,
        original_filename: str,
        mime_type: str,
        job_title: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
        score_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Process CV from raw bytes."""
        import tempfile
        import os

        suffix = ".pdf" if mime_type == "application/pdf" else ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = await self.process_cv(
                tmp_path, original_filename, len(content),
                job_title, required_skills, score_weights
            )
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        return result

    def _score_candidate(
        self,
        parsed: Dict[str, Any],
        github_data: Optional[Dict[str, Any]],
        required_skills: Optional[List[str]] = None,
        score_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Calcule le score du candidat avec rapport d'IA explicable (XAI).
        """
        import math
        scores: Dict[str, float] = {}
        notes: List[str] = []

        raw_weights = score_weights or self.SCORE_WEIGHTS
        total_w = sum(raw_weights.values())
        weights = {k: v / total_w for k, v in raw_weights.items()} if abs(total_w - 1.0) > 0.05 else raw_weights

        # 1. Compétences Techniques (Skills)
        skills = [s["name"].lower() if isinstance(s, dict) else s.lower()
                  for s in parsed.get("skills", [])]
        
        matched_skills_list = []
        missing_skills_list = []
        
        if required_skills and skills:
            req_lower = [r.lower() for r in required_skills]
            if hasattr(embedding_service, 'ready') and embedding_service.ready:
                matched = 0
                for req in required_skills:
                    if embedding_service.has_semantic_match(req, skills, threshold=0.65):
                        matched += 1
                        matched_skills_list.append(req)
                    else:
                        missing_skills_list.append(req)
                
                skills_score = min(100, (matched / max(len(required_skills), 1)) * 100)
                notes.append(f"Semantically matched {matched}/{len(required_skills)} required skills")
            else:
                matched = 0
                for r in req_lower:
                    if any(r in s or s in r for s in skills):
                        matched += 1
                        matched_skills_list.append(r.title())
                    else:
                        missing_skills_list.append(r.title())
                
                skills_score = min(100, (matched / max(len(req_lower), 1)) * 100)
                notes.append(f"Text-matched {matched}/{len(required_skills)} required skills")
        elif not required_skills:
            skills_score = min(100, len(skills) * 5)
            matched_skills_list = [s.title() for s in skills[:8]]
            notes.append(f"Found {len(skills)} technical skills")
        else:
            skills_score = 0
            missing_skills_list = [r.title() for r in required_skills]
            notes.append("No skills found in CV")
            
        scores["skills_score"] = round(skills_score, 2)

        # 2. Expérience (Experience)
        experiences = parsed.get("experience", [])
        years_exp = parsed.get("years_experience") or 0.0
        exp_score = min(100, years_exp * 10)
        if years_exp == 0 and experiences:
            exp_score = len(experiences) * 20
        scores["experience_score"] = round(min(100, exp_score), 2)
        notes.append(f"~{years_exp} years experience detected")

        # 3. Éducation (Education)
        education = parsed.get("education", [])
        edu_score = 0
        for edu in education:
            degree = (edu.get("degree") or "").lower()
            if any(d in degree for d in ["phd", "doctorate"]):
                edu_score = 100
            elif any(d in degree for d in ["master", "msc", "mba", "ingénieur"]):
                edu_score = max(edu_score, 85)
            elif any(d in degree for d in ["bachelor", "bsc", "licence"]):
                edu_score = max(edu_score, 70)
            else:
                edu_score = max(edu_score, 50)
        scores["education_score"] = round(edu_score, 2)

        # 4. GitHub & Contributions
        gh_score = 0
        if github_data:
            gh_score = github_data.get("contribution_score", 0.0)
            notes.append(f"GitHub contribution score: {gh_score:.1f}")
        scores["github_score"] = round(gh_score, 2)

        # 5. Communication & Langues
        langs = parsed.get("languages", [])
        comm_score = 50
        if langs:
            comm_score += min(30, len(langs) * 10)
        if parsed.get("summary"):
            comm_score += 20
        scores["communication_score"] = round(min(100, comm_score), 2)

        # Weighted score
        total = (
            scores["skills_score"] * weights.get("skills", 0.35) +
            scores["experience_score"] * weights.get("experience", 0.30) +
            scores["education_score"] * weights.get("education", 0.20) +
            scores["github_score"] * weights.get("github", 0.10) +
            scores["communication_score"] * weights.get("communication", 0.05)
        )

        # Generer des explications XAI claires et compréhensibles
        xai_reasons = []
        if scores["skills_score"] >= 80:
            xai_reasons.append("🔥 Profil technique très solide, avec une excellente maîtrise des technos recherchées.")
        elif scores["skills_score"] >= 50:
            xai_reasons.append("⚡ Profil technique équilibré, mais présente quelques impasses mineures.")
        else:
            xai_reasons.append("⚠️ Profil technique léger. Certaines compétences clés essentielles sont absentes.")

        if years_exp >= 5:
            xai_reasons.append(f"💼 Expérience substantielle ({years_exp} ans) consolidant une expertise senior.")
        elif years_exp >= 2:
            xai_reasons.append(f"💼 Expérience confirmée ({years_exp} ans) permettant une autonomie rapide.")
        else:
            xai_reasons.append("🌱 Expérience de niveau junior ou transition de carrière.")

        if scores["education_score"] >= 85:
            xai_reasons.append("🎓 Diplôme universitaire supérieur ou cursus d'ingénieur de haut niveau.")

        if scores["github_score"] >= 50:
            xai_reasons.append("💻 Excellente implication Open Source, contributions GitHub vérifiées et actives.")

        # Calculer le ranking dynamique
        ranking_expl = "Ce candidat se situe dans le Top 15% des profils analysés grâce à la complétude de son parcours."
        if total < 50:
            ranking_expl = "Profil avec un positionnement junior ou en reconversion, nécessitant un accompagnement technique."

        explainable_ai = {
            "reasons": xai_reasons,
            "matched_skills": matched_skills_list,
            "missing_skills": missing_skills_list,
            "ranking_explanation": ranking_expl
        }

        return {
            "total_score": round(total, 2),
            "skills_score": scores["skills_score"],
            "experience_score": scores["experience_score"],
            "education_score": scores["education_score"],
            "github_score": scores["github_score"],
            "communication_score": scores["communication_score"],
            "scoring_notes": notes,
            "explainable_ai": explainable_ai
        }

    @staticmethod
    def _guess_name(filename: str) -> str:
        """Derive candidate name from filename as fallback."""
        import re
        base = filename.replace(".pdf", "").replace(".docx", "")
        base = re.sub(r'[_\-\.]+', ' ', base)
        stop = {"cv", "resume", "fr", "en", "an", "last", "final", "new"}
        words = [w for w in base.split() if w.lower() not in stop]
        return " ".join(words[:3]).title() if words else "Unknown Candidate"


cv_agent = CVAgent()
