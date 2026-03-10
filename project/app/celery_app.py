import os
from celery import Celery

# Redis connection URL (default matches docker-compose)
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
REDIS_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

celery_app = Celery(
    "healthops_worker",
    broker=REDIS_URL,
    backend=REDIS_BACKEND,
    include=["app.tasks.execute_workflow", "app.tasks.generate_project"]
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
)
