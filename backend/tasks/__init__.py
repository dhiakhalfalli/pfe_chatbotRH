from .celery_worker import celery_app, process_cv_task

__all__ = ["celery_app", "process_cv_task"]
