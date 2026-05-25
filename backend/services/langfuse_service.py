"""
Langfuse Service: Tracing et monitoring des agents IA.
Permet de superviser les prompts, décisions et performances du système.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Langfuse client (graceful fallback si non configuré) ──────────────────────
try:
    from langfuse import Langfuse
    from backend.config.settings import settings

    if settings.LANGFUSE_SECRET_KEY and settings.LANGFUSE_PUBLIC_KEY:
        langfuse_client = Langfuse(
            secret_key=settings.LANGFUSE_SECRET_KEY,
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            host=settings.LANGFUSE_HOST,
        )
        LANGFUSE_ENABLED = True
        logger.info("✅ Langfuse tracing enabled")
    else:
        langfuse_client = None
        LANGFUSE_ENABLED = False
        logger.info("ℹ️  Langfuse keys not configured – tracing disabled")
except ImportError:
    langfuse_client = None
    LANGFUSE_ENABLED = False
    logger.warning("⚠️  langfuse package not installed – tracing disabled")
except Exception as e:
    langfuse_client = None
    LANGFUSE_ENABLED = False
    logger.warning(f"⚠️  Langfuse init failed: {e}")


# ── Public API ─────────────────────────────────────────────────────────────────

def trace_agent_call(
    agent_name: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> Optional[str]:
    """
    Trace un appel agent dans Langfuse.
    Retourne l'ID du trace créé, ou None si Langfuse est désactivé.
    """
    if not LANGFUSE_ENABLED or not langfuse_client:
        return None
    try:
        trace = langfuse_client.trace(
            name=f"agent.{agent_name}",
            input=input_data,
            output=output_data,
            metadata={
                **(metadata or {}),
                "agent": agent_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            session_id=session_id,
        )
        return trace.id
    except Exception as e:
        logger.debug(f"Langfuse trace failed (non-blocking): {e}")
        return None


def trace_llm_call(
    prompt: str,
    response: str,
    model: str,
    agent_name: str = "unknown",
    metadata: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> Optional[str]:
    """
    Trace un appel LLM (prompt + réponse) dans Langfuse.
    Utile pour analyser la qualité des prompts et détecter les dérives.
    """
    if not LANGFUSE_ENABLED or not langfuse_client:
        return None
    try:
        generation = langfuse_client.generation(
            name=f"llm.{agent_name}",
            model=model,
            input=prompt,
            output=response,
            metadata={
                **(metadata or {}),
                "agent": agent_name,
                "prompt_length": len(prompt),
                "response_length": len(response),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            session_id=session_id,
        )
        return generation.id
    except Exception as e:
        logger.debug(f"Langfuse generation trace failed (non-blocking): {e}")
        return None


def trace_cv_processing(
    candidate_id: str,
    filename: str,
    score: float,
    job_title: Optional[str] = None,
    anonymized: bool = False,
) -> Optional[str]:
    """Trace spécifique au pipeline CV Analysis."""
    return trace_agent_call(
        agent_name="cv_analysis",
        input_data={"filename": filename, "job_title": job_title, "anonymized": anonymized},
        output_data={"score": score, "candidate_id": candidate_id},
        metadata={"pipeline": "cv_processing", "privacy_compliant": anonymized},
        session_id=candidate_id,
    )


def trace_matching(
    candidate_id: str,
    job_id: str,
    score: float,
    matched_skills: list,
    missing_skills: list,
) -> Optional[str]:
    """Trace spécifique au Matching Agent."""
    return trace_agent_call(
        agent_name="matching",
        input_data={"candidate_id": candidate_id, "job_id": job_id},
        output_data={
            "score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
        },
        metadata={"pipeline": "job_matching"},
        session_id=f"{candidate_id}_{job_id}",
    )


def trace_intent_detection(
    query: str,
    intent: str,
    score: float,
    session_id: Optional[str] = None,
) -> Optional[str]:
    """Trace la détection d'intention du routeur."""
    return trace_agent_call(
        agent_name="intent_router",
        input_data={"query": query[:200]},  # tronquer pour éviter les grandes payloads
        output_data={"intent": intent, "confidence_score": score},
        metadata={"pipeline": "intent_detection"},
        session_id=session_id,
    )


def is_enabled() -> bool:
    """Retourne True si Langfuse est actif."""
    return LANGFUSE_ENABLED
