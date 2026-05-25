"""
Duplicate CV Detector: Permet d'éviter le double-scoring
en détectant les CV identiques ou très similaires (par e-mail, téléphone ou ressemblance de texte brut).
"""
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class DuplicateCVDetector:
    """
    Service pour identifier les candidatures dupliquées.
    Aide à maintenir une base de données de recrutement saine et évite de surconsommer les LLMs.
    """

    async def detect_duplicate(
        self,
        email: Optional[str],
        phone: Optional[str],
        raw_text: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Vérifie si un CV est déjà présent dans le système.
        
        Retourne :
        - has_duplicate (bool) : True si doublon détecté
        - duplicate_candidate_id (str) : ID du candidat d'origine
        - reason (str) : Raison du doublon ("email", "phone" ou "text_similarity")
        """
        from backend.database.mongo import MongoDB
        col = MongoDB.get_collection("candidates")

        # 1. Vérification par E-mail
        if email:
            existing = await col.find_one({"email": email.lower().strip()})
            if existing:
                logger.info(f"🔍 Duplicate detected by email: {email}")
                return True, existing.get("id"), "Un candidat avec cet e-mail est déjà inscrit dans le système."

        # 2. Vérification par Téléphone
        if phone:
            # Nettoyer les espaces, tirets et indicatifs
            clean_phone = self._clean_phone(phone)
            if clean_phone:
                cursor = col.find({})
                candidates = await cursor.to_list(length=1000)

                for c in candidates:
                    c_phone = self._clean_phone(c.get("phone"))
                    if c_phone and c_phone == clean_phone:
                        logger.info(f"🔍 Duplicate detected by phone: {phone}")
                        return True, c.get("id"), "Un candidat avec ce numéro de téléphone est déjà enregistré."

        # 3. Vérification par Similitude du texte brut (Fingerprinting)
        if len(raw_text) > 200:
            fingerprint = self._generate_fingerprint(raw_text)
            cursor = col.find({})
            candidates = await cursor.to_list(length=1000)

            for c in candidates:
                c_text = c.get("raw_text", "")
                if len(c_text) > 200:
                    c_fingerprint = self._generate_fingerprint(c_text)
                    # Mesurer la distance de Jaccard simple sur les n-grams
                    similarity = self._jaccard_similarity(fingerprint, c_fingerprint)
                    if similarity > 0.88:
                        logger.info(f"🔍 Duplicate detected by CV text similarity: {similarity:.2f}")
                        return True, c.get("id"), f"Ce CV est identique à 88%+ au profil de {c.get('full_name')}."

        return False, None, None

    def _clean_phone(self, p: Optional[str]) -> str:
        if not p:
            return ""
        # Ne garde que les chiffres
        return "".join(c for c in p if c.isdigit())[-9:]

    def _generate_fingerprint(self, text: str) -> set:
        """Génère des trigrammes de mots pour calculer la ressemblance textuelle."""
        words = [w.strip() for w in text.lower().split() if len(w.strip()) > 2]
        trigrams = set()
        for i in range(len(words) - 2):
            trigrams.add(f"{words[i]}|{words[i+1]}|{words[i+2]}")
        return trigrams

    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union


# Singleton
duplicate_cv_detector = DuplicateCVDetector()
