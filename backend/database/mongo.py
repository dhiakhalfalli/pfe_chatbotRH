"""
MongoDB connection and operations for CV and candidate data.
Uses motor (async MongoDB driver) with a sync fallback using pymongo.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Try async motor first, fall back to sync pymongo
try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    logger.warning("motor not installed, using in-memory store for MongoDB")

try:
    import pymongo
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

from backend.config.settings import settings


class InMemoryStore:
    """Fallback in-memory store when MongoDB is unavailable."""

    def __init__(self):
        self._data: Dict[str, List[Dict[str, Any]]] = {}

    def get_collection(self, name: str) -> "InMemoryCollection":
        if name not in self._data:
            self._data[name] = []
        return InMemoryCollection(self._data[name])


class InMemoryCursor:
    def __init__(self, data: List[Dict[str, Any]], query: Dict[str, Any] = None):
        self._data = data
        self._query = query or {}
        self._sort_key = None
        self._sort_desc = False
        self._limit = None
        self._skip = 0

    def sort(self, key: str, direction: int = -1):
        self._sort_key = key
        self._sort_desc = (direction == -1)
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    def skip(self, n: int):
        self._skip = n
        return self

    def _get_results(self) -> List[Dict[str, Any]]:
        import re

        def matches_val(doc_val, query_val):
            if isinstance(query_val, dict):
                if "$exists" in query_val:
                    return (doc_val is not None) == query_val["$exists"]
                if "$regex" in query_val:
                    pattern = query_val["$regex"]
                    options = query_val.get("$options", "")
                    flags = 0
                    if "i" in options:
                        flags |= re.IGNORECASE
                    try:
                        return bool(re.search(pattern, str(doc_val or ""), flags))
                    except:
                        return False
            return doc_val == query_val

        def get_nested(doc, key):
            if not isinstance(doc, dict):
                return None
            if "." not in key:
                return doc.get(key)
            parts = key.split(".")
            curr = doc
            for i, p in enumerate(parts):
                if isinstance(curr, list):
                    remaining = ".".join(parts[i:])
                    results = []
                    for item in curr:
                        val = get_nested(item, remaining)
                        if isinstance(val, list):
                            results.extend(val)
                        elif val is not None:
                            results.append(val)
                    return results
                if not isinstance(curr, dict):
                    return None
                curr = curr.get(p)
            return curr

        def matches_query(doc, q):
            for k, v in q.items():
                if k == "$or":
                    if not any(matches_query(doc, sub_q) for sub_q in v):
                        return False
                else:
                    doc_val = get_nested(doc, k)
                    if isinstance(doc_val, list):
                        if not any(matches_val(i, v) for i in doc_val):
                            return False
                    elif not matches_val(doc_val, v):
                        return False
            return True

        results = [doc for doc in self._data if matches_query(doc, self._query)]

        # Apply sort
        if self._sort_key:
            results.sort(
                key=lambda x: x.get(self._sort_key) if x.get(self._sort_key) is not None else "",
                reverse=self._sort_desc
            )

        # Apply skip & limit
        start = self._skip
        end = (start + self._limit) if self._limit is not None else None
        return results[start:end]

    def __await__(self):
        async def _exec():
            return self._get_results()
        return _exec().__await__()

    async def to_list(self, length: int = None) -> List[Dict[str, Any]]:
        if length is not None:
            self._limit = length
        return self._get_results()


class InMemoryCollection:
    def __init__(self, data: List[Dict[str, Any]]):
        self._data = data

    async def insert_one(self, doc: Dict[str, Any]) -> Any:
        self._data.append(doc)

        class Result:
            inserted_id = doc.get("id", str(len(self._data)))
        return Result()

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for doc in self._data:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def find(self, query: Dict[str, Any] = None) -> InMemoryCursor:
        return InMemoryCursor(self._data, query)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> None:
        set_data = update.get("$set", {})
        for doc in self._data:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(set_data)
                return

    async def update_many(self, query: Dict[str, Any], update: Dict[str, Any]) -> None:
        set_data = update.get("$set", {})
        for doc in self._data:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(set_data)

    async def count_documents(self, query: Dict[str, Any] = None) -> int:
        if not query:
            return len(self._data)
        return len([d for d in self._data if all(d.get(k) == v for k, v in query.items())])

    async def delete_one(self, query: Dict[str, Any]) -> None:
        for i, doc in enumerate(self._data):
            if all(doc.get(k) == v for k, v in query.items()):
                self._data.pop(i)
                return


class MongoDB:
    """MongoDB client wrapper with async support and in-memory fallback."""

    _client: Optional[Any] = None
    _db: Optional[Any] = None
    _in_memory: Optional[InMemoryStore] = None
    _use_memory: bool = False

    @classmethod
    async def connect(cls) -> None:
        """Initialize connection to MongoDB."""
        if MOTOR_AVAILABLE:
            try:
                cls._client = AsyncIOMotorClient(
                    settings.MONGODB_URL,
                    serverSelectionTimeoutMS=3000
                )
                cls._db = cls._client[settings.MONGODB_DB]
                # Test connection
                await cls._client.admin.command("ping")
                logger.info(f"✅ MongoDB connected: {settings.MONGODB_URL}")
                cls._use_memory = False
                return
            except Exception as e:
                logger.warning(f"⚠️  MongoDB unavailable ({e}), using in-memory store")

        cls._use_memory = True
        cls._in_memory = InMemoryStore()
        logger.info("📦 Using in-memory MongoDB fallback")

    @classmethod
    async def disconnect(cls) -> None:
        if cls._client:
            cls._client.close()
            logger.info("MongoDB disconnected")

    @classmethod
    def get_collection(cls, name: str):
        if cls._use_memory or cls._in_memory:
            return cls._in_memory.get_collection(name)
        if cls._db is None:
            raise RuntimeError("MongoDB not connected. Call MongoDB.connect() first.")
        return cls._db[name]

    # ─── Convenience methods ──────────────────────────────────────────────────

    @classmethod
    async def insert_candidate(cls, candidate: Dict[str, Any]) -> str:
        col = cls.get_collection("candidates")
        candidate["created_at"] = datetime.utcnow().isoformat()
        result = await col.insert_one(candidate)
        return str(result.inserted_id)

    @classmethod
    async def get_candidate(cls, candidate_id: str) -> Optional[Dict[str, Any]]:
        col = cls.get_collection("candidates")
        return await col.find_one({"id": candidate_id})

    @classmethod
    async def update_candidate(cls, candidate_id: str, update_data: Dict[str, Any]) -> None:
        col = cls.get_collection("candidates")
        update_data["updated_at"] = datetime.utcnow().isoformat()
        await col.update_one({"id": candidate_id}, {"$set": update_data})

    @classmethod
    async def list_candidates(cls, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        col = cls.get_collection("candidates")
        if cls._use_memory:
            docs = await col.find({})
            return docs[skip: skip + limit]
        cursor = col.find({}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    @classmethod
    async def insert_cv_document(cls, cv_doc: Dict[str, Any]) -> str:
        col = cls.get_collection("cv_documents")
        result = await col.insert_one(cv_doc)
        return str(result.inserted_id)

    @classmethod
    async def save_candidate_score(cls, score_data: Dict[str, Any]) -> None:
        col = cls.get_collection("candidate_scores")
        await col.insert_one(score_data)

    @classmethod
    async def get_ranked_candidates(cls, limit: int = 50, job_id: Optional[str] = None) -> List[Dict[str, Any]]:
        col = cls.get_collection("candidates")
        
        if not job_id:
            # If no job_id is provided, just return candidates (maybe we shouldn't rank if no job given, but keep backward compat)
            docs = await col.find({}).to_list(length=limit) if not cls._use_memory else await col.find({})
            return docs
            
        # We need candidates who have an offer_evaluation for this job_id
        query = {"offer_evaluations.job_id": job_id}
        
        if cls._use_memory:
            docs = await col.find(query)
            def get_job_score(c):
                evs = c.get("offer_evaluations", [])
                for ev in evs:
                    if ev.get("job_id") == job_id:
                        return ev.get("score", 0)
                return 0
            docs.sort(key=get_job_score, reverse=True)
            return docs[:limit]

        cursor = col.find(query)
        docs = await cursor.to_list(length=1000)
        
        # Sort in python since we need to extract from array
        def get_job_score(c):
            evs = c.get("offer_evaluations", [])
            for ev in evs:
                if ev.get("job_id") == job_id:
                    return ev.get("score", 0)
            return 0
            
        docs.sort(key=get_job_score, reverse=True)
        return docs[:limit]

    @classmethod
    async def insert_job_offer(cls, job_offer: Dict[str, Any]) -> str:
        col = cls.get_collection("job_offers")
        job_offer["created_at"] = datetime.utcnow().isoformat()
        result = await col.insert_one(job_offer)
        return str(result.inserted_id)

    @classmethod
    async def get_job_offer(cls, offer_id: str) -> Optional[Dict[str, Any]]:
        col = cls.get_collection("job_offers")
        return await col.find_one({"id": offer_id})

    @classmethod
    async def update_job_offer(cls, offer_id: str, update_data: Dict[str, Any]) -> None:
        col = cls.get_collection("job_offers")
        update_data["updated_at"] = datetime.utcnow().isoformat()
        await col.update_one({"id": offer_id}, {"$set": update_data})

    @classmethod
    async def list_job_offers(cls, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        col = cls.get_collection("job_offers")
        if cls._use_memory:
            docs = await col.find({})
            return docs[skip: skip + limit]
        cursor = col.find({}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)


# Module-level singleton
mongo = MongoDB()
