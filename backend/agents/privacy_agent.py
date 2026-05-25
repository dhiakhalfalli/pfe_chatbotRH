"""
Privacy Agent: Consentement RGPD, anonymisation PII, suppression auto post-traitement.
"""
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PrivacyAgent:
    SENSITIVE_FIELDS = ["full_name", "email", "phone", "address", "photo_url",
                        "linkedin_url", "date_of_birth", "nationality"]

    CONSENT_DETAILS = {
        "purpose": "Analyse intelligente du profil et classement des candidatures",
        "data_used": ["Compétences", "Expériences", "Formations", "Certifications"],
        "data_masked_from_ai": ["Nom", "Email", "Téléphone", "Photo"],
        "retention_period": "72 heures après traitement",
        "your_rights": ["Accès", "Rectification", "Effacement (Art. 17 RGPD)", "Retrait du consentement"],
        "legal_basis": "Consentement explicite – Article 6(1)(a) RGPD",
    }

    def get_consent_request(self, candidate_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "consent_required": True,
            "candidate_id": candidate_id,
            "message": (
                "Avant d'analyser votre candidature, nous avons besoin de votre consentement "
                "pour l'utilisation temporaire de vos données personnelles."
            ),
            "details": self.CONSENT_DETAILS,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def record_consent(self, candidate_id: str, consented: bool,
                              ip_address: Optional[str] = None) -> Dict[str, Any]:
        from backend.database.mongo import MongoDB
        record = {
            "consent": {
                "consented": consented,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ip_address": ip_address or "unknown",
                "version": "1.0",
            },
            "data_processing_allowed": consented,
        }
        try:
            await MongoDB.update_candidate(candidate_id, record)
            logger.info(f"Consent {'ACCEPTED' if consented else 'REFUSED'} for {candidate_id}")
        except Exception as e:
            logger.error(f"Failed to record consent for {candidate_id}: {e}")
        return {
            "status": "recorded",
            "candidate_id": candidate_id,
            "consented": consented,
            "message": (
                "Consentement enregistré. Vos données seront supprimées automatiquement après 72h."
                if consented else
                "Consentement refusé. Aucune donnée ne sera traitée par l'IA."
            ),
        }

    async def check_consent(self, candidate_id: str) -> bool:
        from backend.database.mongo import MongoDB
        try:
            c = await MongoDB.get_candidate(candidate_id)
            return bool(c and c.get("data_processing_allowed", False))
        except Exception:
            return False

    def anonymize_cv_data(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Masque les PII avant envoi au LLM – réduit aussi les biais de recrutement."""
        a = candidate_data.copy()
        replacements = {
            "full_name": "Candidat(e) Anonyme",
            "email": "***@***.***",
            "phone": "XX XX XX XX XX",
            "address": "[Adresse masquée]",
            "linkedin_url": "[LinkedIn masqué]",
        }
        for field, value in replacements.items():
            if field in a:
                a[field] = value
        for field in ["photo_url", "date_of_birth", "nationality", "marital_status"]:
            a.pop(field, None)

        if s := a.get("summary"):
            s = re.sub(r'\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b', "***@***.***", s)
            s = re.sub(r'(\+?\d[\d\s.\-()]{7,}\d)', "XX XX XX XX XX", s)
            a["summary"] = s

        a["_anonymized"] = True
        a["_anonymized_at"] = datetime.now(timezone.utc).isoformat()
        logger.info("CV data anonymized before LLM processing (bias reduction enabled)")
        return a

    async def delete_sensitive_data(self, candidate_id: str) -> Dict[str, Any]:
        """Supprime les PII post-traitement – Art. 17 RGPD (droit à l'effacement)."""
        from backend.database.mongo import MongoDB
        try:
            await MongoDB.update_candidate(candidate_id, {
                **{field: None for field in self.SENSITIVE_FIELDS},
                "cv_file_path": None,
                "raw_text": None,
                "data_deleted": True,
                "data_deleted_at": datetime.now(timezone.utc).isoformat(),
                "deletion_reason": "Suppression automatique post-traitement IA (72h)",
            })
            logger.info(f"PII deleted for candidate {candidate_id}")
            return {
                "status": "deleted",
                "candidate_id": candidate_id,
                "deleted_fields": self.SENSITIVE_FIELDS + ["cv_file_path", "raw_text"],
                "deleted_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to delete PII for {candidate_id}: {e}")
            return {"status": "error", "candidate_id": candidate_id, "error": str(e)}

    def answer_privacy_question(self, query: str) -> Dict[str, Any]:
        q = query.lower()
        if any(w in q for w in ["supprimer", "effacer", "delete", "oubli"]):
            return {"response": (
                "### 🗑️ Droit à l'effacement (Art. 17 RGPD)\n\n"
                "Vos données sont **supprimées automatiquement 72h** après traitement.\n\n"
                "Vous pouvez aussi demander une suppression immédiate via votre espace candidat."
            )}
        elif any(w in q for w in ["consent", "accord", "autorisation", "consentement"]):
            return {"response": (
                "### ✅ Consentement explicite\n\n"
                "Nous demandons votre accord avant tout traitement IA, "
                "conformément à l'**Article 6(1)(a) du RGPD**.\n\n"
                "Vous pouvez retirer votre consentement à tout moment."
            )}
        elif any(w in q for w in ["anonymi", "masqu", "pii"]):
            return {"response": (
                "### 🔒 Anonymisation\n\n"
                "Vos données personnelles (nom, email, téléphone) sont **masquées** "
                "avant l'analyse IA.\nSeuls vos compétences et expériences sont analysés, "
                "ce qui réduit également les **biais de recrutement**."
            )}
        return {"response": (
            "### 🔐 Protection des données personnelles\n\n"
            "Notre plateforme respecte le **RGPD** :\n\n"
            "1. **Consentement explicite** avant tout traitement\n"
            "2. **Anonymisation** des PII avant l'IA\n"
            "3. **Suppression automatique** après 72h\n"
            "4. **Transparence totale** sur l'utilisation de vos données"
        )}


privacy_agent = PrivacyAgent()
