"""
LangGraph Orchestrator: Routes HR requests to specialized agents.
Implements a state machine graph with intent detection and agent routing.
"""
import logging
import re
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import date, datetime
import operator

logger = logging.getLogger(__name__)

# ─── LangGraph imports (graceful fallback) ────────────────────────────────────
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
from backend.agents.onboarding_agent import onboarding_agent
from backend.agents.training_agent import training_agent
from backend.agents.payroll_agent import payroll_agent
from backend.agents.leave_agent import leave_agent
from backend.agents.segula_agent import segula_agent


# ─── State definition ─────────────────────────────────────────────────────────

class HRState(TypedDict):
    """State passed between nodes in the LangGraph workflow."""
    query: str
    intent: str
    agent_called: str
    result: Dict[str, Any]
    employee_id: Optional[str]
    candidate_id: Optional[str]
    metadata: Dict[str, Any]
    messages: Annotated[List[Dict[str, str]], operator.add]
    error: Optional[str]


# ─── Intent patterns ──────────────────────────────────────────────────────────

INTENT_PATTERNS: Dict[str, List[str]] = {
    "analyse_cv": [
        r"analys[ei] cv", r"process cv", r"score candidate",
        r"upload cv", r"cv analysis", r"parse cv", r"evaluate (cv|resume)",
        r"analyse (cv|resume)", r"check (cv|resume)", r"profile", r"skills",
        r"details", r"about (this |the )?candidate", r"who is (he|she)",
        r"comp[ée]tences", r"d[ée]tails", r"profil", r"qui est", r"son parcours",
    ],
    "plan_interview": [
        r"interview question", r"schedule interview", r"plan interview",
        r"interview plan", r"interview candidate", r"generate question",
        r"interview prep", r"technical question",
    ],
    "employee_onboarding": [
        r"onboard", r"new hire", r"welcome (employee|new|hire)",
        r"onboarding plan", r"new employee", r"first day",
        r"employee setup", r"checklist for",
    ],
    "find_candidates": [
        r"find candidate", r"looking for candidate", r"search candidate",
        r"match cv", r"suitable profile", r"hire", r"matching between",
        r"how to match", r"matching logic", r"candidate for", r"profiles for", 
        r"who (can|should) we hire",
    ],
    "training_recommendation": [
        r"train", r"learning", r"course", r"skill gap", r"upskill",
        r"recommend training", r"development plan", r"improve skill",
        r"what (course|training)", r"learn",
    ],
    "payroll_question": [
        r"salary", r"payslip", r"pay slip", r"payroll", r"deduction",
        r"net (salary|pay|income)", r"tax", r"bonus", r"compensation",
        r"how much (do i|am i|will i)", r"take home", r"401k",
    ],
    "leave_request": [
        r"leave", r"vacation", r"time off", r"annual leave", r"sick leave",
        r"leave balance", r"days off", r"holiday", r"absent",
        r"request (leave|time|vacation)", r"submit leave",
    ],
    "segula_general": [
        r"segula", r"company policy", r"hr policy", r"general question",
        r"values", r"benefits", r"culture", r"who are we", r"about segula"
    ]
}


class HROrchestrator:
    """
    Central orchestrator that detects intent and routes to specialized agents.
    Uses LangGraph when available, falls back to simple routing.
    """

    def __init__(self):
        self._graph = None
        if LANGGRAPH_AVAILABLE:
            self._build_graph()

    def _build_graph(self) -> None:
        """Build the LangGraph state machine."""
        graph = StateGraph(HRState)

        # ── Nodes ──────────────────────────────────────────────────────────────
        graph.add_node("detect_intent", self._detect_intent_node)
        graph.add_node("cv_agent", self._cv_node)
        graph.add_node("interview_agent", self._interview_node)
        graph.add_node("onboarding_agent", self._onboarding_node)
        graph.add_node("training_agent", self._training_node)
        graph.add_node("payroll_agent", self._payroll_node)
        graph.add_node("leave_agent", self._leave_node)
        graph.add_node("recruitment_agent", self._recruitment_node)
        graph.add_node("segula_agent", self._segula_node)
        graph.add_node("fallback", self._fallback_node)

        # ── Entry point ────────────────────────────────────────────────────────
        graph.set_entry_point("detect_intent")

        # ── Routing ────────────────────────────────────────────────────────────
        graph.add_conditional_edges(
            "detect_intent",
            self._route,
            {
                "analyse_cv": "cv_agent",
                "plan_interview": "interview_agent",
                "employee_onboarding": "onboarding_agent",
                "training_recommendation": "training_agent",
                "payroll_question": "payroll_agent",
                "leave_request": "leave_agent",
                "find_candidates": "recruitment_agent",
                "segula_general": "segula_agent",
                "unknown": "fallback",
            },
        )

        # ── Terminal edges ─────────────────────────────────────────────────────
        for node in ["cv_agent", "interview_agent", "onboarding_agent",
                     "training_agent", "payroll_agent", "leave_agent", 
                     "recruitment_agent", "segula_agent", "fallback"]:
            graph.add_edge(node, END)

        memory = MemorySaver()
        self._graph = graph.compile(checkpointer=memory)
        logger.info("LangGraph orchestrator compiled successfully")

    # ─── Node implementations ─────────────────────────────────────────────────

    def _detect_intent_node(self, state: HRState) -> HRState:
        """Detect the user's intent from their query."""
        intent = self.detect_intent(state["query"])
        state["intent"] = intent
        state["messages"].append({
            "role": "system",
            "content": f"Intent detected: {intent}",
        })
        return state

    def _route(self, state: HRState) -> str:
        """Route to the appropriate agent based on detected intent."""
        return state.get("intent", "unknown")

    async def _cv_node(self, state: HRState) -> HRState:
        state["agent_called"] = "cv_agent"
        candidate_id = state.get("candidate_id")
        logger.info(f"CV Node called for candidate_id: {candidate_id}")
        
        if candidate_id:
            from backend.database.mongo import MongoDB
            candidate = await MongoDB.get_candidate(candidate_id)
            if candidate:
                logger.info(f"Found candidate: {candidate.get('full_name')}")
                skills = [s["name"] if isinstance(s, dict) else s for s in candidate.get("skills", [])]
                score = candidate.get("score", {}).get("total_score", 0)
                
                response = (
                    f"### 📄 Candidate Profile: **{candidate.get('full_name')}**\n\n"
                    f"**AI Fit Score:** {score}%\n"
                    f"**Applied For:** {candidate.get('job_title_applied', 'N/A')}\n\n"
                    f"**Top Skills:** {', '.join(skills[:8])}\n\n"
                    f"**Summary:** {candidate.get('summary', 'No summary available.')}\n\n"
                    f"**Experience:** {candidate.get('years_experience', 0)} years total.\n\n"
                    "Would you like me to generate interview questions for this candidate or recommend some training programs?"
                )
                state["result"] = {"response": response, "candidate": candidate}
                return state
            else:
                logger.warning(f"Candidate not found in DB: {candidate_id}")

        state["result"] = {
            "agent": "cv_agent",
            "message": "CV processing requires file upload via /upload_cv endpoint, or select a candidate first.",
            "status": "redirect",
        }
        return state

    def _interview_node(self, state: HRState) -> HRState:
        state["agent_called"] = "interview_agent"
        candidate_id = state.get("candidate_id", "demo")
        meta = state.get("metadata", {})
        result = interview_agent.generate_questions(
            candidate_id=candidate_id,
            skills=meta.get("skills", ["python", "machine learning"]),
            job_title=meta.get("job_title", "Software Engineer"),
            experience_years=meta.get("experience_years", 3),
            num_questions=meta.get("num_questions", 8),
        )
        state["result"] = result
        return state

    def _onboarding_node(self, state: HRState) -> HRState:
        state["agent_called"] = "onboarding_agent"
        meta = state.get("metadata", {})
        result = onboarding_agent.create_onboarding_plan(
            employee_id=state.get("employee_id", "emp001"),
            employee_name=meta.get("employee_name", "New Employee"),
            department=meta.get("department", "Engineering"),
            job_title=meta.get("job_title", "Software Engineer"),
            start_date=date.today(),
            manager_name=meta.get("manager_name"),
        )
        state["result"] = result
        return state

    def _training_node(self, state: HRState) -> HRState:
        state["agent_called"] = "training_agent"
        meta = state.get("metadata", {})
        employee_id = state.get("employee_id", "emp001")
        result = training_agent.analyze_and_recommend(
            employee_id=employee_id,
            current_skills=meta.get("skills", []),
            job_title=meta.get("job_title", ""),
            required_skills=meta.get("required_skills"),
            career_goal=meta.get("career_goal"),
        )
        state["result"] = result
        return state

    def _payroll_node(self, state: HRState) -> HRState:
        state["agent_called"] = "payroll_agent"
        result = payroll_agent.answer_question(
            question=state["query"],
            employee_id=state.get("employee_id"),
        )
        state["result"] = result
        return state

    def _leave_node(self, state: HRState) -> HRState:
        state["agent_called"] = "leave_agent"
        meta = state.get("metadata", {})
        query = state["query"].lower()

        # Determine action
        if any(kw in query for kw in ["submit", "request", "apply", "take"]):
            action = "submit"
        elif any(kw in query for kw in ["balance", "how many", "remaining", "left"]):
            action = "check_balance"
        elif any(kw in query for kw in ["history", "list", "previous"]):
            action = "list"
        else:
            action = "summary"

        result = leave_agent.handle_request(
            action=action,
            employee_id=state.get("employee_id", "emp001"),
            leave_type=meta.get("leave_type"),
            start_date=meta.get("start_date"),
            end_date=meta.get("end_date"),
            reason=meta.get("reason"),
        )
        state["result"] = result
        return state

    def _recruitment_node(self, state: HRState) -> HRState:
        state["agent_called"] = "recruitment_agent"
        state["result"] = {
            "finding_candidates": True,
            "response": (
                "### 🔍 AI Candidate-Job Matching\n\n"
                "Our platform uses a multi-agent system to match candidates with job offers:\n\n"
                "1. **CV Processing**: The **CV Agent** extracts technical skills and experience levels from uploaded files.\n"
                "2. **Requirement Alignment**: Candidates are scored against the specific requirements of each job position.\n"
                "3. **Ranking**: You can see the results in the **Candidate Ranking** page, where candidates are sorted by their AI fit score.\n\n"
                "**How to use it:**\n"
                "• Go to the **Job Positions** page.\n"
                "• Click on **'View Candidates'** on any job card to see only the candidates matched for that specific role.\n"
                "• Or go directly to **Candidate Ranking** to see all candidates across all positions."
            )
        }
        return state

    def _segula_node(self, state: HRState) -> HRState:
        state["agent_called"] = "segula_agent"
        # Since this is an external user prompt forced through the explicit intent flag, 
        # let's extract query and ask the ollama LLM directly:
        result = segula_agent.answer_general(state["query"])
        state["result"] = result
        return state

    def _fallback_node(self, state: HRState) -> HRState:
        state["agent_called"] = "fallback"
        state["result"] = {
            "response": (
                "👋 **Hello! I'm your HR Assistant.**\n\n"
                "I can help you with:\n"
                "• 📄 **CV Analysis** – Upload and score candidate CVs\n"
                "• 🎤 **Interview Planning** – Generate interview questions\n"
                "• 🚀 **Employee Onboarding** – Create onboarding plans\n"
                "• 📚 **Training** – Recommend learning programs\n"
                "• 💰 **Payroll** – Answer salary and payment questions\n"
                "• 🏖️ **Leave Management** – Check balance, submit requests\n\n"
                "Try asking: *'What is my leave balance?'* or *'Generate interview questions for a Python developer'*"
            ),
        }
        return state

    # ─── Public API ───────────────────────────────────────────────────────────

    def detect_intent(self, query: str) -> str:
        """Detect intent from a user query string."""
        query_lower = query.lower().strip()

        best_intent = "unknown"
        best_score = 0

        for intent, patterns in INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            if score > best_score:
                best_score = score
                best_intent = intent

        logger.debug(f"Intent detected: {best_intent} (score={best_score}) for query: {query[:60]}")
        return best_intent

    async def process(
        self,
        query: str,
        employee_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        thread_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Main entry point: process an HR query and return a response.
        """
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
                logger.error(f"LangGraph execution failed: {e}, falling back to simple router")

        # ── Fallback: simple routing ────────────────────────────────────────
        return await self._simple_route(initial_state)

    async def _simple_route(self, state: HRState) -> Dict[str, Any]:
        """Simple routing without LangGraph."""
        intent = self.detect_intent(state["query"])

        handlers = {
            "cv_agent": self._cv_node,
            "interview_agent": self._interview_node,
            "onboarding_agent": self._onboarding_node,
            "training_agent": self._training_node,
            "payroll_agent": self._payroll_node,
            "leave_agent": self._leave_node,
            "recruitment_agent": self._recruitment_node,
            "segula_agent": self._segula_node,
        }

        routing = {
            "analyse_cv": "cv_agent",
            "plan_interview": "interview_agent",
            "employee_onboarding": "onboarding_agent",
            "training_recommendation": "training_agent",
            "payroll_question": "payroll_agent",
            "leave_request": "leave_agent",
            "find_candidates": "recruitment_agent",
            "segula_general": "segula_agent",
        }

        state["intent"] = intent
        node_name = routing.get(intent, "fallback")

        import inspect
        if node_name in handlers:
            handler = handlers[node_name]
            if inspect.iscoroutinefunction(handler):
                state = await handler(state)
            else:
                state = handler(state)
        else:
            state = self._fallback_node(state)

        return {
            "intent": intent,
            "agent": state["agent_called"],
            "result": state["result"],
            "query": state["query"],
        }


# Module singleton
orchestrator = HROrchestrator()
