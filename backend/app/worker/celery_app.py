import logging
from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

celery_app = Celery(
    "internpilot_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    # Periodic Celery Beat schedule for automation infrastructure
    beat_schedule={
        "heartbeat-every-minute": {
            "task": "jobs.scheduled_heartbeat_task",
            "schedule": 60.0,  # Runs every 60 seconds
        },
    },
)


def inspect_workers_online() -> dict:
    """
    Probes Celery worker availability using the celery control inspector.
    Returns status and active worker node names.
    """
    try:
        inspector = celery_app.control.inspect(timeout=1.5)
        ping_res = inspector.ping()
        if ping_res and len(ping_res) > 0:
            return {
                "status": "connected",
                "active_workers": list(ping_res.keys()),
                "worker_count": len(ping_res),
            }
        return {
            "status": "disconnected",
            "active_workers": [],
            "worker_count": 0,
            "details": "No active Celery workers responded to ping",
        }
    except Exception as exc:
        return {
            "status": "disconnected",
            "active_workers": [],
            "worker_count": 0,
            "error": str(exc),
        }
