"""
Embedding Service for Semantic Routing and Skill Matching.
Uses local sentence-transformers model to prevent API costs.
"""
import logging
from typing import List, Union
import numpy as np

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers or scikit-learn not installed. Semantic matching will fallback to exact matching.")

class EmbeddingService:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model = None
        self.ready = False
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # all-MiniLM-L6-v2 is small and very fast for sentences and keywords
                logger.debug(f"Loading embedding model {model_name}...")
                self.model = SentenceTransformer(model_name)
                self.ready = True
                logger.info(f"Embedding model '{model_name}' loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")

    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Convert text or list of texts into vector embeddings.
        Returns a numpy array of embeddings.
        """
        if not self.ready:
            raise RuntimeError("Embedding model is not loaded.")
            
        if isinstance(texts, str):
            texts = [texts]
            
        return self.model.encode(texts)

    def compute_similarity(self, query: str, candidates: List[str]) -> List[float]:
        """
        Compute cosine similarity between a single query and a list of candidates.
        Returns a list of similarity scores between 0 and 1.
        """
        if not self.ready or not candidates:
            return [0.0] * len(candidates)
            
        query_embedding = self.embed(query)
        candidate_embeddings = self.embed(candidates)
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]
        
        # Convert to standard Python float list
        return [float(score) for score in similarities]

    def has_semantic_match(self, query: str, candidates: List[str], threshold: float = 0.65) -> bool:
        """
        Check if the query matches any of the candidates above the given threshold.
        """
        if not self.ready or not candidates:
            return False
            
        scores = self.compute_similarity(query, candidates)
        return any(score >= threshold for score in scores)

# Singleton instance
embedding_service = EmbeddingService()
