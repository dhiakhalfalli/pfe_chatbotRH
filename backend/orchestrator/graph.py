"""
LangGraph Orchestrator: Routes les requêtes de recrutement vers les agents spécialisés.
Architecture recentrée sur le recrutement intelligent avec Privacy Agent intégré.
"""
import logging
import re
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import date, datetime
import operator

logger = logging.getLogger(__name__)

# ─── LangGraph (graceful fallback) ───────────────────────────────────────────
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
    logger.info("LangGraph available")
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not installed – using simple router fallback")

from backend.agents.cv_agent import cv_agent
from backend.agents.interview_agent import interview_agent
from backend.agents.privacy_agent import privacy_agent
from backend.agents.rh_assistant_agent import rh_assistant_agent
from backend.agents.segula_agent import segula_agent  # RAG / base documentaire
from backend.services.llm_service import generate_response
from backend.services.embedding_service import embedding_service


# ─── State ────────────────────────────────────────────────────────────────────

class HRState(TypedDict):
    query: str
    intent: str
    agent_called: str
    result: Dict[str, Any]
    employee_id: Optional[str]
    candidate_id: Optional[str]
    metadata: Dict[str, Any]
    messages: Annotated[List[Dict[str, str]], operator.add]
    error: Optional[str]


# ─── Intent patterns (recrutement + privacy) ──────────────────────────────────

INTENT_PATTERNS: Dict[str, List[str]] = {
    "analyse_cv": [
        "Please analyze this candidate's CV and profile",
        "What are the skills of this candidate?",
        "Can you score this candidate?",
        "Tell me about this candidate's background and experience",
        "Fais-moi un résumé de l'expérience de ce candidat",
        "Quelles sont les compétences de ce profil ?",
        "Résume ce candidat",
        "Analyse ce CV",
    ],
    "plan_interview": [
        "Generate interview questions for this position",
        "Prepare a technical interview plan",
        "What questions should I ask this candidate?",
        "Prépare des questions d'entretien",
        "Génère des questions pour un développeur",
        "Questions techniques pour ce poste",
        "Entretien pour ce candidat",
    ],
    "find_candidates": [
        "Find candidates suitable for this job profile",
        "Match CVs to the job description",
        "Who should we hire for this position?",
        "Trouve-moi des candidats pour ce poste",
        "Classement des candidats",
        "Meilleurs candidats pour l'offre",
        "Comparer les profils",
    ],
    "privacy_request": [
        "Supprimer mes données personnelles",
        "Je veux effacer mes informations",
        "Consentement pour l'utilisation de mes données",
        "RGPD droits sur mes données",
        "Anonymiser mon profil",
        "Comment mes données sont utilisées ?",
        "Retirer mon consentement",
        "Delete my personal data",
        "Privacy data consent",
    ],
    "rh_assistant": [
        "Résumé des candidatures pour ce poste",
        "Quels sont les meilleurs candidats ?",
        "Aide-moi à choisir un candidat",
        "Prochaines étapes pour ce recrutement",
        "Statistiques des candidatures",
        "Que faire avec ce candidat ?",
        "Recommande-moi un candidat",
        "Analyse du pipeline de recrutement",
    ],
    "rag_hr": [
        "Quelle est la politique de recrutement ?",
        "Processus de recrutement de l'entreprise",
        "Questions sur l'entreprise et les offres",
        "What are the HR policies?",
        "Tell me about the company",
        "Informations sur le processus de candidature",
        "Comment postuler ?",
    ],
}


class HROrchestrator:
    """
    Orchestrateur central – détecte l'intention et route vers l'agent approprié.
    Architecture multi-agents orientée recrutement intelligent.
    """

    def __init__(self):
        self._graph = None
        if LANGGRAPH_AVAILABLE:
            self._build_graph()

    def _build_graph(self) -> None:
        graph = StateGraph(HRState)

        # ── Nœuds ─────────────────────────────────────────────────────────────
        graph.add_node("detect_intent",    self._detect_intent_node)
        graph.add_node("cv_agent",         self._cv_node)
        graph.add_node("interview_agent",  self._interview_node)
        graph.add_node("matching_agent",   self._matching_node)
        graph.add_node("privacy_agent",    self._privacy_node)
        graph.add_node("rh_assistant",     self._rh_assistant_node)
        graph.add_node("rag_agent",        self._rag_node)
        graph.add_node("external_agent",   self._external_node)
        graph.add_node("fallback",         self._fallback_node)

        graph.set_entry_point("detect_intent")

        # ── Routing ────────────────────────────────────────────────────────────
        graph.add_conditional_edges(
            "detect_intent",
            self._route,
            {
                "analyse_cv":      "cv_agent",
                "plan_interview":  "interview_agent",
                "find_candidates": "matching_agent",
                "privacy_request": "privacy_agent",
                "rh_assistant":    "rh_assistant",
                "rag_hr":          "rag_agent",
                "unknown":         "fallback",
            },
        )

        for node in ["cv_agent", "interview_agent", "matching_agent",
                     "privacy_agent", "rh_assistant", "rag_agent", "external_agent", "fallback"]:
            graph.add_edge(node, END)

        memory = MemorySaver()
        self._graph = graph.compile(checkpointer=memory)
        logger.info("LangGraph orchestrator compiled – 6 recruitment agents ready")

    # ─── Nœud : détection d'intention ────────────────────────────────────────

    def _detect_intent_node(self, state: HRState) -> HRState:
        intent = self.detect_intent(state["query"])
        state["intent"] = intent
        state["messages"].append({"role": "system", "content": f"Intent: {intent}"})
        return state

    def _route(self, state: HRState) -> str:
        role = state.get("metadata", {}).get("role", "hr")
        intent = state.get("intent", "unknown")
        
        if role == "external":
            if intent == "privacy_request":
                return "privacy_agent"
            return "external_agent"
            
        return intent

    # ─── Nœud : CV Agent ─────────────────────────────────────────────────────

    async def _cv_node(self, state: HRState) -> HRState:
        state["agent_called"] = "cv_agent"
        candidate_id = state.get("candidate_id")

        if candidate_id:
            from backend.database.mongo import MongoDB
            candidate = await MongoDB.get_candidate(candidate_id)
            if candidate:
                skills = [s["name"] if isinstance(s, dict) else s for s in candidate.get("skills", [])]
                score = candidate.get("score", {}).get("total_score", 0)
                role = state.get("metadata", {}).get("role", "hr")

                # Anonymiser si mode candidat
                display_name = candidate.get("full_name", "N/A")
                if role == "external":
                    display_name = "Votre profil"

                candidate_context = (
                    f"Name: {display_name}\n"
                    f"AI Fit Score: {score}%\n"
                    f"Applied For: {candidate.get('job_title_applied', 'N/A')}\n"
                    f"Skills: {', '.join(skills)}\n"
                    f"Experience: {candidate.get('years_experience', 0)} years\n"
                    f"Summary: {candidate.get('summary', 'N/A')}"
                )

                llm_response = generate_response(
                    system_prompt=(
                        f"Tu es un assistant RH expert. Rôle utilisateur: '{role}'. "
                        f"Réponds en markdown de façon professionnelle.\n\n"
                        f"--- PROFIL CANDIDAT ---\n{candidate_context}"
                    ),
                    user_prompt=state.get("query", "Résume ce candidat"),
                )

                state["result"] = {
                    "response": llm_response or (
                        f"### 📄 Profil: **{display_name}**\n\n"
                        f"**Score IA:** {score}%\n"
                        f"**Poste visé:** {candidate.get('job_title_applied', 'N/A')}\n"
                        f"**Compétences:** {', '.join(skills[:8])}\n"
                        f"**Expérience:** {candidate.get('years_experience', 0)} ans"
                    ),
                    "candidate": candidate,
                }
                return state

        state["result"] = {
            "response": (
                "📄 **Analyse de CV**\n\nPour analyser un CV, utilisez l'endpoint "
                "`/upload_cv` ou sélectionnez un candidat depuis la liste."
            )
        }
        return state

    # ─── Nœud : Interview Agent ───────────────────────────────────────────────

    async def _interview_node(self, state: HRState) -> HRState:
        state["agent_called"] = "interview_agent"
        meta = state.get("metadata", {})
        query = state.get("query", "")
        skills, job_title, experience_years = meta.get("skills", []), meta.get("job_title", ""), meta.get("experience_years", 0)
        candidate_name, candidate_summary = "", ""

        if not job_title:
            job_title = self._extract_job_title_from_query(query)

        candidate_id = state.get("candidate_id")
        if candidate_id:
            try:
                from backend.database.mongo import MongoDB
                candidate = await MongoDB.get_candidate(candidate_id)
                if candidate:
                    candidate_name = candidate.get("full_name", "")
                    candidate_summary = candidate.get("summary", "")
                    if not skills:
                        skills = [s["name"] if isinstance(s, dict) else s for s in candidate.get("skills", [])]
                    if not job_title:
                        job_title = candidate.get("job_title_applied", "Software Engineer")
                    if not experience_years:
                        experience_years = candidate.get("years_experience", 0)
            except Exception as e:
                logger.error(f"Failed to fetch candidate for interview: {e}")

        if not job_title:
            job_title = "Software Engineer"

        result = interview_agent.generate_questions(
            candidate_id=candidate_id or "general",
            skills=skills,
            job_title=job_title,
            experience_years=experience_years,
            num_questions=meta.get("num_questions", 8),
            candidate_name=candidate_name,
            candidate_summary=candidate_summary,
        )
        state["result"] = result
        return state

    # ─── Nœud : Matching Agent ────────────────────────────────────────────────

    def _matching_node(self, state: HRState) -> HRState:
        state["agent_called"] = "matching_agent"
        state["result"] = {
            "response": (
                "### 🎯 Matching Candidats – Offres\n\n"
                "Notre système multi-agents classe automatiquement les candidats "
                "selon leur compatibilité avec chaque offre :\n\n"
                "1. **CV Agent** – Extraction intelligente des compétences\n"
                "2. **Matching Agent** – Score de compatibilité candidat/offre\n"
                "3. **Privacy Agent** – Anonymisation des données avant analyse\n\n"
                "**Accéder aux résultats :**\n"
                "- Page **Candidats** → classement global\n"
                "- Page **Offres** → *'Voir les candidats'* pour une offre spécifique\n"
                "- **API** : `POST /jobs/{job_id}/rank-all`"
            )
        }
        return state

    # ─── Nœud : Privacy Agent ─────────────────────────────────────────────────

    async def _privacy_node(self, state: HRState) -> HRState:
        state["agent_called"] = "privacy_agent"
        query = state.get("query", "")
        candidate_id = state.get("candidate_id")

        # Demande de suppression explicite
        if any(w in query.lower() for w in ["supprimer", "effacer", "delete", "oubli"]):
            if candidate_id:
                result = await privacy_agent.delete_sensitive_data(candidate_id)
                state["result"] = {
                    "response": (
                        f"### 🗑️ Données supprimées\n\n"
                        f"Les données personnelles du candidat `{candidate_id}` ont été "
                        f"anonymisées conformément au **RGPD (Art. 17)**.\n\n"
                        f"**Champs supprimés :** Nom, email, téléphone, adresse, photo\n"
                        f"**Conservés :** Compétences, score, expérience agrégée"
                    )
                }
                return state

        # Réponse générale sur la privacy
        result = privacy_agent.answer_privacy_question(query)
        state["result"] = result
        return state

    # ─── Nœud : RH Assistant ─────────────────────────────────────────────────

    async def _rh_assistant_node(self, state: HRState) -> HRState:
        state["agent_called"] = "rh_assistant"
        query = state.get("query", "")
        candidate_id = state.get("candidate_id")
        meta = state.get("metadata", {})

        context = {}
        if candidate_id:
            try:
                from backend.database.mongo import MongoDB
                candidate = await MongoDB.get_candidate(candidate_id)
                if candidate:
                    context["candidate"] = candidate
            except Exception as e:
                logger.error(f"Failed to fetch candidate for rh_assistant: {e}")

        result = rh_assistant_agent.answer(query, context=context)
        state["result"] = result
        return state

    # ─── Nœud : RAG Agent (base documentaire) ────────────────────────────────

    def _rag_node(self, state: HRState) -> HRState:
        state["agent_called"] = "rag_agent"
        result = segula_agent.answer_general(state["query"])
        state["result"] = result
        return state

    # ─── Nœud : External Agent (Candidat) ────────────────────────────────────

    async def _external_node(self, state: HRState) -> HRState:
        state["agent_called"] = "external_agent"
        query = state.get("query", "")
        meta = state.get("metadata", {})
        email = meta.get("email")
        
        candidate = None
        if email:
            from backend.database.mongo import MongoDB
            col = MongoDB.get_collection("candidates")
            candidate = await col.find_one({"email": email})
        
        candidate_context = ""
        if candidate:
            status_map = {
                "pending": "En attente d'examen RH (CV bien reçu)",
                "shortlisted": "Shortlisté 🎉 (Un recruteur va vous contacter pour un entretien)",
                "rejected": "Non retenu pour le moment (Profil conservé pour de futures opportunités)",
                "review": "En cours d'évaluation par l'équipe de recrutement"
            }
            c_status = status_map.get(candidate.get("status", "pending"), "Inconnu")
            skills = [s["name"] if isinstance(s, dict) else s for s in candidate.get("skills", [])]
            
            candidate_context = (
                f"\n--- PROFIL DU CANDIDAT ACTUEL ---\n"
                f"Statut actuel de la candidature: {c_status}\n"
                f"Compétences extraites du CV: {', '.join(skills)}\n"
                f"Expérience: {candidate.get('years_experience', 0)} ans\n"
                f"Poste visé: {candidate.get('job_title_applied', 'N/A')}\n"
            )
        else:
            candidate_context = "\n--- PROFIL DU CANDIDAT ---\nAucun CV n'a été déposé ou associé à cet email. Le candidat doit d'abord uploader un CV pour le suivi ou le matching.\n"

        jobs_context = ""
        try:
            from backend.database.mongo import MongoDB
            jobs = await MongoDB.list_job_offers()
            jobs_list = []
            for j in jobs:
                j_skills = ", ".join(j.get("criteria", {}).get("must_have_skills", []))
                jobs_list.append(f"- {j.get('title')} (Compétences: {j_skills})")
            jobs_context = "\n--- OFFRES D'EMPLOI ACTUELLES ---\n" + "\n".join(jobs_list)
        except Exception as e:
            logger.warning(f"Failed to fetch jobs for external agent: {e}")

        system_prompt = (
            "Tu es l'Assistant Virtuel et Ambassadeur Marque Employeur de Segula Technologies, dédié exclusivement aux candidats.\n"
            "Tu dois répondre aux requêtes de manière bienveillante, chaleureuse et très professionnelle.\n\n"
            "🚀 **TES 4 MISSIONS PRINCIPALES :**\n"
            "1. **Coach d'Entretien (Interview Prep)** : Si le candidat te demande de le préparer pour un poste (ex: 'Prépare-moi pour un poste de Dev Python'), "
            "tu DOIS te transformer en coach technique. Pose-lui 3 questions techniques précises (typiques de Segula) et donne 2 conseils comportementaux.\n"
            "2. **Orientation / Matching inversé** : Si le candidat demande 'Quelles offres me correspondent ?', analyse ses compétences et "
            "donne le Top 3 des offres actuelles les plus adaptées en justifiant ton choix. S'il n'a pas déposé de CV, dis-lui de le faire.\n"
            "3. **Suivi de candidature** : S'il demande 'Où en est ma candidature ?', donne-lui son statut exact avec bienveillance.\n"
            "4. **FAQ Entreprise & Culture** : Agis comme ambassadeur. Segula Technologies propose généralement : jusqu'à 3 jours de télétravail/semaine, "
            "des tickets restaurant, une mutuelle avantageuse, et un processus de recrutement en 3 étapes (Appel RH, Test Technique, Entretien Manager).\n\n"
            f"{candidate_context}\n"
            f"{jobs_context}\n\n"
            "⚠️ **RÈGLES STRICTES :**\n"
            "- Utilise un formatage markdown riche (titres, listes à puces, mots en gras, emojis 🎯✨💡).\n"
            "- Ne donne jamais d'informations sur les notes internes, les recruteurs ou les autres candidats.\n"
            "- Sois concis mais percutant."
        )

        try:
            llm_response = generate_response(system_prompt=system_prompt, user_prompt=query)
        except Exception as e:
            logger.error(f"External agent LLM error: {e}")
            llm_response = None

        if not llm_response:
            llm_response = (
                "👋 **Bonjour ! Je suis votre assistant recrutement Segula Technologies.**\n\n"
                "Je peux vous aider à :\n"
                "- 📄 **Analyser votre CV** – Obtenez un score et des recommandations\n"
                "- 🎤 **Préparer votre entretien** – Questions personnalisées\n"
                "- 📋 **Suivre votre candidature** – Statut et prochaines étapes\n"
                "- 🔒 **Gérer vos données** – Consentement et suppression RGPD\n\n"
                "*Essayez : 'Analyse mon profil' ou 'Prépare-moi pour un entretien Python'*"
            )
            
        state["result"] = {"response": llm_response}
        return state

    # ─── Nœud : Fallback ──────────────────────────────────────────────────────

    async def _fallback_node(self, state: HRState) -> HRState:
        state["agent_called"] = "fallback"
        query = state.get("query", "")
        role = state.get("metadata", {}).get("role", "hr")
        candidate_id = state.get("candidate_id")

        candidate_context = ""
        if candidate_id:
            try:
                from backend.database.mongo import MongoDB
                candidate = await MongoDB.get_candidate(candidate_id)
                if candidate:
                    skills = [s["name"] if isinstance(s, dict) else s for s in candidate.get("skills", [])]
                    score = candidate.get("score", {}).get("total_score", 0)
                    candidate_context = (
                        f"\n\n--- CANDIDAT SÉLECTIONNÉ ---\n"
                        f"Score IA: {score}% | Poste: {candidate.get('job_title_applied', 'N/A')}\n"
                        f"Compétences: {', '.join(skills)}\n"
                        f"Expérience: {candidate.get('years_experience', 0)} ans\n"
                        f"Résumé: {candidate.get('summary', 'N/A')}"
                    )
            except Exception as e:
                logger.error(f"Failed to fetch candidate context: {e}")

        system_prompt = (
            "Tu es un assistant RH expert pour une plateforme de recrutement intelligente. "
            f"Rôle utilisateur: '{role}'. "
        )
        if role == "external":
            system_prompt += (
                "L'utilisateur est un CANDIDAT. Aide-le avec sa candidature, "
                "la préparation d'entretien et le suivi de sa candidature. "
                "Ne divulgue pas d'informations sur les autres candidats. "
            )
        else:
            system_prompt += (
                "L'utilisateur est un RECRUTEUR RH. Il peut accéder aux données "
                "des candidats, aux offres et aux statistiques. "
            )
        system_prompt += (
            "Réponds en markdown de façon professionnelle et concise (max 4 paragraphes)."
            + candidate_context
        )

        if query.strip():
            llm_response = generate_response(system_prompt=system_prompt, user_prompt=query)
            if llm_response:
                state["result"] = {"response": llm_response}
                return state

        # Fallback statique
        if role == "external":
            state["result"] = {
                "response": (
                    "👋 **Bonjour ! Je suis votre assistant recrutement.**\n\n"
                    "Je peux vous aider à :\n"
                    "- 📄 **Analyser votre CV** – Obtenez un score et des recommandations\n"
                    "- 🎤 **Préparer votre entretien** – Questions personnalisées\n"
                    "- 📋 **Suivre votre candidature** – Statut et prochaines étapes\n"
                    "- 🔒 **Gérer vos données** – Consentement et suppression RGPD\n\n"
                    "*Essayez : 'Analyse mon profil' ou 'Prépare-moi pour un entretien Python'*"
                )
            }
        else:
            state["result"] = {
                "response": (
                    "👋 **Assistant RH – Recrutement Intelligent**\n\n"
                    "Je peux vous aider avec :\n"
                    "- 📄 **Analyse CV** – Score et résumé automatique\n"
                    "- 🎯 **Matching** – Compatibilité candidat/offre\n"
                    "- 🎤 **Entretien** – Génération de questions techniques\n"
                    "- 📊 **Statistiques** – Pipeline de recrutement\n"
                    "- 🔒 **Privacy** – Gestion RGPD des candidatures\n\n"
                    "*Essayez : 'Résume les candidatures pour le poste Python'*"
                )
            }
        return state

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_job_title_from_query(query: str) -> str:
        q = query.strip()
        patterns = [
            r"(?:for\s+(?:a|an|the)\s+)(.+?)(?:\s+position|\s+role|\s+interview|\s*$)",
            r"(?:for\s+)(.+?)(?:\s+position|\s+role|\s+interview|\s*$)",
            r"^(?:generate\s+|prepare\s+|create\s+)?(.+?)\s+interview\s+question",
            r"interview\s+(?:question|prep).*?(?:for|about)\s+(?:a\s+|an\s+|the\s+)?(.+?)$",
            r"questions?\s+(?:pour|de|d')\s+(?:un\s+|une\s+)?(.+?)$",
        ]
        for pat in patterns:
            m = re.search(pat, q, re.IGNORECASE)
            if m:
                title = m.group(1).strip().strip("?.,!")
                if len(title) > 1 and title.lower() not in {"me", "this", "the", "a"}:
                    return title
        return ""

    # ─── Détection d'intention (Semantic Router) ──────────────────────────────

    def detect_intent(self, query: str) -> str:
        if not query.strip():
            return "unknown"

        best_intent = "unknown"
        best_score = 0.0

        if not hasattr(embedding_service, "ready") or not embedding_service.ready:
            query_lower = query.lower()
            for intent, patterns in INTENT_PATTERNS.items():
                for pattern in patterns:
                    if any(word in query_lower for word in pattern.lower().split()):
                        if best_score < 0.5:
                            best_score = 0.5
                            best_intent = intent
            return best_intent

        for intent, anchor_phrases in INTENT_PATTERNS.items():
            scores = embedding_service.compute_similarity(query, anchor_phrases)
            max_score = max(scores) if scores else 0.0
            if max_score > best_score:
                best_score = float(max_score)
                best_intent = intent

        if best_score < 0.45:
            best_intent = "unknown"

        logger.debug(f"Intent: {best_intent} (score={best_score:.3f}) | query: {query[:60]}")
        return best_intent

    # ─── Entrée publique ──────────────────────────────────────────────────────

    async def process(
        self,
        query: str,
        employee_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        thread_id: str = "default",
    ) -> Dict[str, Any]:
        initial_state: HRState = {
            "query": query,
            "intent": "",
            "agent_called": "",
            "result": {},
            "employee_id": employee_id,
            "candidate_id": candidate_id,
            "metadata": metadata or {},
            "messages": [{"role": "user", "content": query}],
            "error": None,
        }

        if LANGGRAPH_AVAILABLE and self._graph:
            try:
                config = {"configurable": {"thread_id": thread_id}}
                final_state = await self._graph.ainvoke(initial_state, config)
                return {
                    "intent": final_state["intent"],
                    "agent": final_state["agent_called"],
                    "result": final_state["result"],
                    "query": query,
                }
            except Exception as e:
                logger.error(f"LangGraph error: {e}, falling back to simple router")

        return await self._simple_route(initial_state)

    async def _simple_route(self, state: HRState) -> Dict[str, Any]:
        intent = self.detect_intent(state["query"])
        state["intent"] = intent
        role = state.get("metadata", {}).get("role", "hr")

        if role == "external":
            if intent == "privacy_request":
                return await self._privacy_node(state)
            return await self._external_node(state)

        handlers = {
            "analyse_cv":      self._cv_node,
            "plan_interview":  self._interview_node,
            "find_candidates": self._matching_node,
            "privacy_request": self._privacy_node,
            "rh_assistant":    self._rh_assistant_node,
            "rag_hr":          self._rag_node,
        }

        import inspect
        handler = handlers.get(intent)
        if handler:
            state = await handler(state) if inspect.iscoroutinefunction(handler) else handler(state)
        else:
            state = await self._fallback_node(state)

        return {
            "intent": intent,
            "agent": state["agent_called"],
            "result": state["result"],
            "query": state["query"],
        }


# Singleton
orchestrator = HROrchestrator()
