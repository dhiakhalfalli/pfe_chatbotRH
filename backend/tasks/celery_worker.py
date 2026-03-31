"""
Celery Worker: Async task processing for CV analysis, scoring, and GitHub analysis.
"""
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not installed – background tasks will run synchronously")

from backend.config.settings import settings

# ─── Celery app ───────────────────────────────────────────────────────────────

if CELERY_AVAILABLE:
    celery_app = Celery(
        "hr_platform",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
    )

    @celery_app.task(bind=True, max_retries=3, name="tasks.process_cv")
    def process_cv_task(
        self,
        file_path: str,
        original_filename: str,
        file_size: int,
        job_title: Optional[str] = None,
        required_skills: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Async CV processing task.
        Runs OCR, parsing, GitHub analysis, and scoring.
        """
        import asyncio
        from backend.agents.cv_agent import cv_agent

        try:
            logger.info(f"Processing CV task: {original_filename}")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                cv_agent.process_cv(
                    file_path, original_filename, file_size, job_title, required_skills
                )
            )
            loop.close()
            logger.info(f"CV task complete: {result.get('candidate_id')}")
            return result
        except Exception as exc:
            logger.error(f"CV task failed: {exc}")
            self.retry(exc=exc, countdown=60)

    @celery_app.task(bind=True, max_retries=3, name="tasks.analyze_github")
    def analyze_github_task(
        self,
        candidate_id: str,
        github_url: str,
    ) -> Dict[str, Any]:
        """Async GitHub profile analysis task."""
        from backend.tools.github_tool import github_tool
        import asyncio
        from backend.database.mongo import MongoDB

        try:
            profile = github_tool.fetch_profile(github_url)
            if profile:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    MongoDB.update_candidate(
                        candidate_id,
                        {"github_profile": profile}
                    )
                )
                loop.close()
            return {"candidate_id": candidate_id, "github_profile": profile}
        except Exception as exc:
            logger.error(f"GitHub task failed: {exc}")
            self.retry(exc=exc, countdown=30)

    @celery_app.task(name="tasks.batch_score_cvs")
    def batch_score_cvs_task(job_title: str, required_skills: list) -> Dict[str, Any]:
        """Re-score all candidates for a specific job posting."""
        import asyncio
        from backend.database.mongo import MongoDB
        from backend.agents.cv_agent import cv_agent

        async def _run():
            candidates = await MongoDB.list_candidates(limit=500)
            updated = 0
            for candidate in candidates:
                if candidate.get("raw_text"):
                    parsed = {"skills": candidate.get("skills", []),
                              "experience": candidate.get("experience", []),
                              "education": candidate.get("education", []),
                              "languages": candidate.get("languages", []),
                              "summary": candidate.get("summary"),
                              "years_experience": candidate.get("years_experience")}
                    score = cv_agent._score_candidate(parsed, None, required_skills)
                    await MongoDB.update_candidate(candidate["id"], {"score": score})
                    updated += 1
            return updated

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        count = loop.run_until_complete(_run())
        loop.close()
        return {"job_title": job_title, "candidates_scored": count}

else:
    # ── Stub when Celery is not available ──────────────────────────────────────
    class _SyncTask:
        """Simple synchronous stub for Celery tasks."""
        def __init__(self, func):
            self.func = func
            self.task_id = "sync"

        def delay(self, *args, **kwargs):
            result = self.func(*args, **kwargs)

            class FakeResult:
                id = "sync-task"
                status = "SUCCESS"

                def get(self, timeout=None):
                    return result

            return FakeResult()

        def apply_async(self, args=None, kwargs=None, **options):
            return self.delay(*(args or []), **(kwargs or {}))

    def process_cv_task_sync(file_path, original_filename, file_size, job_title=None, required_skills=None):
        import asyncio
        from backend.agents.cv_agent import cv_agent
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            cv_agent.process_cv(file_path, original_filename, file_size, job_title, required_skills)
        )
        loop.close()
        return result

    process_cv_task = _SyncTask(process_cv_task_sync)

    class FakeCeleryApp:
        def task(self, *args, **kwargs):
            def decorator(f): return f
            return decorator

    celery_app = FakeCeleryApp()
