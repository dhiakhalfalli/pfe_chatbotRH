"""
RH Assistant Agent: Assistant conversationnel intelligent dédié au recruteur HR (Copilot IA).
Fournit des résumés, analyses, comparaisons et recommandations avancées sur les candidatures.
"""
import logging
from typing import Optional, Dict, Any, List
from backend.services.llm_service import generate_response

logger = logging.getLogger(__name__)


class RHAssistantAgent:
    """
    Agent assistant pour le recruteur RH.
    Répond aux questions sur les candidats, les offres et les statistiques.
    """

    SYSTEM_PROMPT = (
        "Tu es un assistant RH expert pour une plateforme de recrutement intelligente. "
        "Tu aides les recruteurs à analyser les candidatures, comparer les profils, "
        "générer des shortlists et des argumentaires d'embauche ou de refus basés uniquement sur les compétences. "
        "Tes réponses sont professionnelles, précises et orientées données. "
        "Utilise le markdown pour structurer tes réponses de manière esthétique."
    )

    def answer(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Répond à une question du recruteur avec contexte optionnel."""
        context_str = ""
        if context:
            if candidate := context.get("candidate"):
                skills = [s["name"] if isinstance(s, dict) else s for s in candidate.get("skills", [])]
                context_str = (
                    f"\n\n--- CONTEXTE CANDIDAT ---\n"
                    f"Nom: {candidate.get('full_name', 'N/A')}\n"
                    f"Score IA: {candidate.get('score', {}).get('total_score', 0)}%\n"
                    f"Poste visé: {candidate.get('job_title_applied', 'N/A')}\n"
                    f"Compétences: {', '.join(skills[:10])}\n"
                    f"Expérience: {candidate.get('years_experience', 0)} ans\n"
                    f"Résumé: {candidate.get('summary', 'N/A')}\n"
                )
            if job := context.get("job"):
                context_str += (
                    f"\n--- CONTEXTE OFFRE ---\n"
                    f"Poste: {job.get('title', 'N/A')}\n"
                    f"Compétences requises: {', '.join(job.get('criteria', {}).get('must_have_skills', []))}\n"
                    f"Expérience min: {job.get('criteria', {}).get('min_years_experience', 0)} ans\n"
                )

        response = generate_response(
            system_prompt=self.SYSTEM_PROMPT + context_str,
            user_prompt=query,
        )

        if not response:
            response = self._static_fallback(query)

        return {"response": response, "agent": "rh_assistant"}

    def compare_candidates(self, c1: Dict[str, Any], c2: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un comparatif détaillé côte-à-côte de deux candidats."""
        skills1 = [s["name"] if isinstance(s, dict) else s for s in c1.get("skills", [])]
        skills2 = [s["name"] if isinstance(s, dict) else s for s in c2.get("skills", [])]

        system_prompt = (
            self.SYSTEM_PROMPT +
            "\nTu dois générer une comparaison extrêmement rigoureuse, objective et structurée."
        )

        user_prompt = f"""Compare ces deux candidats pour le poste {c1.get('job_title_applied', 'Software Engineer')} :

Candidat 1:
- Nom: {c1.get('full_name', 'N/A')}
- Score Global: {c1.get('score', {}).get('total_score', 0)}%
- Expérience: {c1.get('years_experience', 0)} ans
- Compétences principales: {', '.join(skills1[:10])}
- Éducation: {[edu.get('degree') for edu in c1.get('education', [])]}

Candidat 2:
- Nom: {c2.get('full_name', 'N/A')}
- Score Global: {c2.get('score', {}).get('total_score', 0)}%
- Expérience: {c2.get('years_experience', 0)} ans
- Compétences principales: {', '.join(skills2[:10])}
- Éducation: {[edu.get('degree') for edu in c2.get('education', [])]}

Génère une réponse structurée en markdown :
1. Tableau comparatif synthétique
2. Points forts / Points faibles de chacun
3. Match de compétences (communes, exclusives)
4. Recommandation finale du Copilot (Lequel choisir et pourquoi ?)"""

        response = generate_response(system_prompt, user_prompt)
        if not response:
            response = "### ⚖️ Comparaison impossible\n\nLes données fournies sont insuffisantes."

        return {"response": response}

    def suggest_shortlist(self, candidates: List[Dict[str, Any]], job_title: str) -> Dict[str, Any]:
        """Suggère automatiquement une shortlist classée avec explications claires."""
        if not candidates:
            return {"response": "Aucun candidat disponible pour concevoir une shortlist."}

        # Trier par score d'abord
        sorted_cands = sorted(candidates, key=lambda x: x.get("score", {}).get("total_score", 0), reverse=True)
        
        candidates_summary = []
        for i, c in enumerate(sorted_cands[:5], 1):
            skills = [s["name"] if isinstance(s, dict) else s for s in c.get("skills", [])]
            candidates_summary.append(
                f"- **Rang {i}**: {c.get('full_name')} | Score: {c.get('score', {}).get('total_score', 0)}% | Exp: {c.get('years_experience', 0)} ans | Skills: {', '.join(skills[:5])}"
            )

        system_prompt = self.SYSTEM_PROMPT + "\nTu es chargé de suggérer une shortlist et de justifier tes choix de manière stratégique."
        user_prompt = f"""Analyse ces candidats pour le poste de **{job_title}** et suggère une Shortlist finale (Top 3 recommandés) :

Candidats disponibles :
{chr(10).join(candidates_summary)}

Fournis :
1. La Shortlist Recommandée (Top 3) avec justification pour chacun.
2. Un plan d'entretien suggéré pour le numéro 1.
3. Pourquoi certains candidats avec des scores proches ont été classés différemment."""

        response = generate_response(system_prompt, user_prompt)
        if not response:
            response = "### 🏆 Shortlist Recommandée\n\n" + "\n".join(candidates_summary[:3])

        return {"response": response}

    def explain_rejection(self, c: Dict[str, Any], job_title: str) -> Dict[str, Any]:
        """Génère un retour constructif et bienveillant expliquant le rejet du candidat."""
        skills = [s["name"] if isinstance(s, dict) else s for s in c.get("skills", [])]
        
        system_prompt = (
            self.SYSTEM_PROMPT +
            "\nTu dois générer une explication éthique, constructive et respectueuse pour aider le candidat à s'améliorer."
        )
        
        user_prompt = f"""Rédige une note explicative interne sur le rejet du candidat {c.get('full_name')} pour le poste {job_title} :
- Score global : {c.get('score', {}).get('total_score', 0)}%
- Expérience : {c.get('years_experience', 0)} ans
- Compétences trouvées : {', '.join(skills[:8])}
- Raison principale : Manque de compétences clés exigées par l'offre.

Génère :
1. Une justification RH claire de la décision (gaps de compétences spécifiques).
2. Un brouillon d'e-mail bienveillant et constructif à envoyer au candidat contenant les axes d'amélioration recommandés pour l'avenir (Employer Branding)."""

        response = generate_response(system_prompt, user_prompt)
        if not response:
            response = f"### ⚠️ Décision de refus\nLe profil de {c.get('full_name')} ne correspondait pas aux prérequis techniques."

        return {"response": response}

    def generate_recruitment_summary(self, candidates: List[Dict], job_title: str = "") -> Dict[str, Any]:
        """Génère un résumé automatique des candidatures pour une offre."""
        if not candidates:
            return {"response": "Aucun candidat à analyser pour ce poste."}

        total = len(candidates)
        # Handle different schemas
        scores = []
        for c in candidates:
            s = c.get("total_score")
            if s is None and isinstance(c.get("score"), dict):
                s = c["score"].get("total_score")
            scores.append(s or 0)
            
        avg_score = sum(scores) / total if total else 0
        
        def key_func(x):
            s = x.get("total_score")
            if s is None and isinstance(x.get("score"), dict):
                s = x["score"].get("total_score")
            return s or 0
            
        top3 = sorted(candidates, key=key_func, reverse=True)[:3]

        summary_lines = [
            f"### 📊 Résumé global du recrutement{' — ' + job_title if job_title else ''}",
            f"\n**{total} candidat(s)** analysé(s) | Score moyen : **{avg_score:.1f}%**\n",
            "#### 🏆 Top 3 candidats recommandés :\n",
        ]
        for i, c in enumerate(top3, 1):
            skills = c.get("top_skills") or [s["name"] if isinstance(s, dict) else s for s in c.get("skills", [])]
            score_val = c.get("total_score")
            if score_val is None and isinstance(c.get("score"), dict):
                score_val = c["score"].get("total_score")
            summary_lines.append(
                f"{i}. **{c.get('full_name', 'N/A')}** — "
                f"Score: {score_val or 0}% | "
                f"Exp: {c.get('years_experience', 0)} ans | "
                f"Skills: {', '.join(skills[:4])}"
            )

        shortlisted = sum(1 for c in candidates if c.get("status") == "shortlisted")
        if shortlisted:
            summary_lines.append(f"\n✅ **{shortlisted} candidat(s) shortlisté(s)**")

        return {"response": "\n".join(summary_lines), "stats": {
            "total": total,
            "avg_score": round(avg_score, 1),
            "shortlisted": shortlisted,
        }}

    def suggest_next_steps(self, candidate: Dict, job: Optional[Dict] = None) -> Dict[str, Any]:
        """Suggère les prochaines étapes du processus de recrutement."""
        score = candidate.get("score", {}).get("total_score", 0) if isinstance(candidate.get("score"), dict) else candidate.get("total_score", 0)
        status = candidate.get("status", "pending")
        name = candidate.get("full_name", "Ce candidat")

        if score >= 75:
            steps = [
                f"✅ **{name}** a un excellent profil (score {score}%)",
                "1. **Planifier un entretien technique** – utiliser l'Interview Agent pour préparer les questions",
                "2. **Envoyer une invitation** via la plateforme",
                "3. **Shortlister** le candidat pour suivi prioritaire",
            ]
        elif score >= 50:
            steps = [
                f"🔶 **{name}** a un profil correct (score {score}%)",
                "1. **Analyser les compétences manquantes** par rapport au poste",
                "2. **Entretien RH préliminaire** pour évaluer la motivation",
                "3. **Décision** selon les résultats de l'entretien",
            ]
        else:
            steps = [
                f"⚠️ **{name}** a un profil insuffisant (score {score}%)",
                "1. **Envoyer un refus courtois** avec feedback constructif",
                "2. **Conserver en base** pour des offres futures si pertinent",
            ]

        return {"response": "\n".join(steps), "recommended_status": (
            "shortlisted" if score >= 75 else "review" if score >= 50 else "rejected"
        )}

    def _static_fallback(self, query: str) -> str:
        return (
            "### 💼 Assistant RH\n\n"
            "Je peux vous aider avec :\n\n"
            "- **Analyse de candidats** : *'Résume le profil de ce candidat'*\n"
            "- **Comparaison** : *'Compare les 3 meilleurs candidats pour ce poste'*\n"
            "- **Prochaines étapes** : *'Que faire avec ce candidat ?'*\n"
            "- **Statistiques** : *'Combien de candidats avons-nous pour le poste X ?'*\n"
            "- **Questions d'entretien** : *'Génère des questions pour un Dev Python'*\n"
        )


# Singleton
rh_assistant_agent = RHAssistantAgent()
