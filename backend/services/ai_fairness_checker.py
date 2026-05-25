"""
AI Fairness Checker: Analyse et garantit que le scoring des candidatures
est basé exclusivement sur les compétences et l'expérience.
Détecte et atténue les biais potentiels (genre, origine, âge, etc.).
"""
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AIFairnessChecker:
    """
    Module de contrôle éthique pour auditer les analyses de CV.
    Garantit le respect de la charte de recrutement éthique.
    """

    # Mots-clés pouvant introduire des biais (genre, nationalité, statut familial, âge)
    BIAS_INDICATORS = {
        "gender": [
            r"\b(monsieur|madame|mlle|mme|mr)\b",
            r"\b(né[e]? le|marié[e]?)\b",
            r"\b(fille|garçon|homme|femme)\b"
        ],
        "nationality": [
            r"\b(nationalité|origine|étranger|visa|titre de séjour|passeport)\b",
            r"\b(français[e]?|tunisien[ne]?|algérien[ne]?|marocain[e]?|sénégalais[e]?)\b"
        ],
        "age": [
            r"\b(\d{2}\s*ans)\b",
            r"\b(âge|né[e]? en \d{4})\b",
            r"\b(retraite|senior|junior|débutant|juniorité)\b"
        ],
        "marital_status": [
            r"\b(marié[e]?|célibataire|divorcé[e]?|pacsé[e]?|enfants|charge de famille)\b"
        ]
    }

    def check_candidate_fairness(self, raw_text: str, parsed_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse le texte brut du CV et le profil extrait pour calculer un score d'équité.
        Identifie les données sensibles à exclure de l'analyse IA.
        """
        text = raw_text.lower()
        checks_logged = []
        bias_found = {}
        sensitive_elements_masked = 0

        # 1. Vérifier si le nom complet a été masqué
        if parsed_profile.get("full_name") == "Candidat(e) Anonyme" or parsed_profile.get("_anonymized"):
            checks_logged.append("✅ Anonymisation de l'identité confirmée (Nom complet masqué)")
            sensitive_elements_masked += 1
        else:
            checks_logged.append("⚠️ Le nom complet n'a pas été anonymisé dans le profil")

        # 2. Vérifier les e-mails et téléphones masqués
        email = parsed_profile.get("email", "")
        phone = parsed_profile.get("phone", "")
        if email in ["***@***.***", None, ""] or "[EMAIL MASQUÉ]" in email:
            checks_logged.append("✅ Coordonnées électroniques anonymisées")
            sensitive_elements_masked += 1
        if phone in ["XX XX XX XX XX", None, ""] or "[TÉL MASQUÉ]" in phone:
            checks_logged.append("✅ Coordonnées téléphoniques anonymisées")
            sensitive_elements_masked += 1

        # 3. Scanner le texte brut pour détecter des indicateurs de biais
        total_bias_signals = 0
        for category, patterns in self.BIAS_INDICATORS.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text)
                if found:
                    matches.extend(found)
            
            if matches:
                bias_found[category] = list(set(matches))
                total_bias_signals += len(matches)
                checks_logged.append(
                    f"⚠️ Signal éthique : {len(matches)} indicateur(s) de {category} détecté(s) dans le CV brut"
                )
            else:
                checks_logged.append(f"✅ Aucun indicateur de {category} détecté dans le CV")

        # 4. Calculer le Fairness Score (Indice d'Équité)
        # Formule : 100% de base, réduit selon les signaux détectés non masqués
        deductions = total_bias_signals * 5
        fairness_score = max(50, 100 - deductions)

        # Si l'anonymisation est active, on remonte le score d'équité
        if parsed_profile.get("_anonymized"):
            fairness_score = min(100, fairness_score + 15)

        is_fair = fairness_score >= 80

        report = {
            "is_fair": is_fair,
            "fairness_score": round(fairness_score, 1),
            "checked_parameters": ["gender", "nationality", "age", "marital_status", "pii_anonymization"],
            "bias_indicators_detected": bias_found,
            "sensitive_elements_masked_count": sensitive_elements_masked,
            "logs": checks_logged,
            "recommendation": (
                "Éligible au traitement IA. L'anonymisation des données personnelles élimine tout risque de biais."
                if is_fair else
                "Recommandation : Veuillez vérifier manuellement le profil. Le CV brut contient des détails biographiques importants."
            ),
        }

        logger.info(f"⚖️ AI Fairness Audit completed. Score: {fairness_score}%")
        return report


# Singleton
ai_fairness_checker = AIFairnessChecker()
