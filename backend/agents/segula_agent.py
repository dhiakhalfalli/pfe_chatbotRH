"""
Segula HR Agent – Answers general HR and company questions.
Uses Ollama if available, otherwise falls back to a smart built-in knowledge base.
"""
import logging
from typing import Dict, Any, Optional
from backend.config.settings import settings

logger = logging.getLogger(__name__)

# ── LLM Management (Dynamic Initialization) ───────────────────────────────────
GROQ_AVAILABLE = False
_groq_llm = None
OLLAMA_AVAILABLE = False
_ollama_llm = None

def get_groq_llm():
    global GROQ_AVAILABLE, _groq_llm
    if _groq_llm:
        return _groq_llm
    
    if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your-groq-api-key-here":
        try:
            from langchain_groq import ChatGroq
            _groq_llm = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model_name="llama-3.3-70b-versatile",
                temperature=0.5,
            )
            GROQ_AVAILABLE = True
            logger.info("✅ Groq LLM initialized")
            return _groq_llm
        except Exception as e:
            logger.warning(f"Groq initialization failed: {e}")
    return None

def get_ollama_llm():
    global OLLAMA_AVAILABLE, _ollama_llm
    if _ollama_llm:
        return _ollama_llm
        
    try:
        import requests
        from langchain_community.llms import Ollama
        # Fast ping check
        resp = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=1)
        if resp.status_code == 200:
            _ollama_llm = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.LLM_MODEL,
                timeout=6000,
            )
            OLLAMA_AVAILABLE = True
            return _ollama_llm
    except:
        pass
    return None

# Decide inference priority based on LLM_PROVIDER in .env
# If provider is groq → prefer Groq over Ollama
_prefer_groq = settings.LLM_PROVIDER.lower() == "groq"



# ── RAG System (FAISS + HuggingFace) ──────────────────────────────────────────
import os
from pathlib import Path

# Provide a fallback generic message
FALLBACK_MESSAGE = (
    "👋 **Hello! I'm the Segula Technologies HR Assistant.**\n\n"
    "I currently don't have enough information in my knowledge base to answer that. "
    "Please try asking about Segula's benefits, leave policy, or how to apply!"
)

class SegulaRAGAgent:
    """
    HR RAG Agent that answers general Segula/HR questions.
    Uses FAISS + HuggingFace for RAG, queries Ollama → Groq.
    """
    def __init__(self):
        self.vector_store = None
        self.kb_dir = Path("backend/knowledge_base")
        # No more _init_rag() in __init__ to allow instant startup

    def _init_rag(self):
        """Initialize the FAISS vector store from local markdown/text files."""
        try:
            from langchain_community.document_loaders import DirectoryLoader, TextLoader
            from langchain_community.vectorstores import FAISS
            from langchain_huggingface import HuggingFaceEmbeddings
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            
            # Create indexing directory if needed
            self.kb_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Loading knowledge base documents from {self.kb_dir}...")
            # Load text and MD files
            loader = DirectoryLoader(str(self.kb_dir), glob="**/*.*", loader_cls=TextLoader)
            documents = loader.load()
            
            if not documents:
                logger.warning("No documents found in knowledge base. RAG will not have context.")
                return

            # Split text
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = text_splitter.split_documents(documents)
            
            # Create embeddings
            logger.info("Generating embeddings for RAG (HuggingFace)...")
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            
            # Build Vector Store
            self.vector_store = FAISS.from_documents(texts, embeddings)
            logger.info(f"✅ FAISS Vector store initialized with {len(texts)} chunks.")
        except Exception as e:
            logger.error(f"Failed to initialize RAG vector store: {e}")

    def answer_general(self, query: str) -> Dict[str, Any]:
        """Answer a general HR/Segula question using RAG."""
        
        # 0. Lazy-init RAG if not already done
        if self.vector_store is None:
            self._init_rag()

        context = ""
        # 1. Retrieve Context from FAISS
        if self.vector_store:
            try:
                retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
                docs = retriever.invoke(query)
                context = "\n\n".join([doc.page_content for doc in docs])
            except Exception as e:
                logger.error(f"FAISS retrieval failed: {e}")

        # Construct RAG Prompt
        prompt_text = (
            "You are the official Segula Technologies HR Assistant. "
            "You answer questions specifically about Segula HR policies, company overview, "
            "employee benefits, and general HR rules based on the provided CONTEXT.\n"
            "If the answer is not in the context, say you don't know politely but offer "
            "general help about Segula HR.\n"
            "Keep answers professional, friendly, and concise (under 4 paragraphs). Use markdown bullet points when helpful.\n\n"
            f"--- CONTEXT ---\n{context if context else 'No context available.'}\n\n"
            f"--- USER QUESTION ---\n{query}\n\n"
            "Answer:"
        )

        def _try_groq(prompt: str):
            llm = get_groq_llm()
            if not llm:
                return None
            try:
                from langchain_core.messages import HumanMessage, SystemMessage
                messages = [
                    SystemMessage(content="You are the official Segula Technologies HR Assistant using RAG context to answer."),
                    HumanMessage(content=prompt),
                ]
                resp = llm.invoke(messages)
                return {"response": resp.content}
            except Exception as e:
                logger.error(f"❌ Groq inference error: {e}")
                return None

        def _try_ollama(prompt: str):
            llm = get_ollama_llm()
            if not llm:
                return None
            try:
                resp = llm.invoke(prompt)
                return {"response": resp}
            except Exception as e:
                logger.error(f"❌ Ollama inference error: {e}")
                return None

        # Choose order based on .env LLM_PROVIDER setting
        if _prefer_groq:
            result = _try_groq(prompt_text) or _try_ollama(prompt_text)
        else:
            result = _try_ollama(prompt_text) or _try_groq(prompt_text)

        if result:
            return result

        # 4. Fallback if no LLMs are active, but we have RAG text
        if context:
            return {
                "response": "📄 **Here is the information I found in my knowledge base:**\n\n" + context
            }

        # 5. Total failure fallback
        return {"response": FALLBACK_MESSAGE}

segula_agent = SegulaRAGAgent()
