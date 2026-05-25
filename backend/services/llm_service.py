"""
Shared LLM Service – Centralised access to Groq / Ollama for all agents.
Priority order is controlled by LLM_PROVIDER in .env.
"""
import logging
from typing import Optional

from backend.config.settings import settings

logger = logging.getLogger(__name__)

# ── Lazy singletons ───────────────────────────────────────────────────────────
_groq_llm = None
_ollama_llm = None


def _get_groq():
    global _groq_llm
    if _groq_llm is not None:
        return _groq_llm
    if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your-groq-api-key-here":
        try:
            from langchain_groq import ChatGroq
            _groq_llm = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model_name="llama-3.3-70b-versatile",
                temperature=0.7,
            )
            logger.info("✅ Groq LLM ready (llm_service)")
            return _groq_llm
        except Exception as e:
            logger.warning(f"Groq init failed: {e}")
    return None


def _get_ollama():
    global _ollama_llm
    if _ollama_llm is not None:
        return _ollama_llm
    try:
        import requests
        from langchain_community.llms import Ollama
        resp = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=1)
        if resp.status_code == 200:
            _ollama_llm = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.LLM_MODEL,
                timeout=6000,
            )
            logger.info("✅ Ollama LLM ready (llm_service)")
            return _ollama_llm
    except Exception:
        pass
    return None


_prefer_groq = settings.LLM_PROVIDER.lower() == "groq"


def generate_response(
    system_prompt: str,
    user_prompt: str,
) -> Optional[str]:
    """
    Send a system + user prompt to the best available LLM and return the
    response text.  Returns None when no LLM is reachable.
    """

    def _try_groq() -> Optional[str]:
        llm = _get_groq()
        if not llm:
            return None
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            resp = llm.invoke(messages)
            return resp.content
        except Exception as e:
            logger.error(f"Groq inference error: {e}")
            return None

    def _try_ollama() -> Optional[str]:
        llm = _get_ollama()
        if not llm:
            return None
        try:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            resp = llm.invoke(full_prompt)
            return resp
        except Exception as e:
            logger.error(f"Ollama inference error: {e}")
            return None

    if _prefer_groq:
        return _try_groq() or _try_ollama()
    else:
        return _try_ollama() or _try_groq()
