import time
from datetime import datetime, timezone
import redis.asyncio as aioredis
from app.core.config import get_settings
from app.db.session import check_database_connection
from app.worker.celery_app import inspect_workers_online
from app.modules.health.schemas import (
    HealthStatusResponse,
    ServiceComponentStatus,
    WorkerHealthStatus,
)

settings = get_settings()


async def check_redis_queue_connection() -> dict:
    """
    Checks Redis broker/queue connectivity and records round-trip ping latency.
    """
    start_time = time.perf_counter()
    client = None
    try:
        redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
        client = aioredis.from_url(redis_url, socket_timeout=2.0)
        pong = await client.ping()
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        if pong:
            return {
                "status": "connected",
                "latency_ms": latency_ms,
                "details": "Redis queue responding normally",
            }
        return {
            "status": "degraded",
            "latency_ms": latency_ms,
            "details": "Redis ping returned false",
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "disconnected",
            "latency_ms": latency_ms,
            "error": str(exc),
        }
    finally:
        if client:
            await client.aclose()


def check_worker_cluster() -> dict:
    """
    Probes Celery worker availability.
    """
    return inspect_workers_online()


async def get_system_health() -> HealthStatusResponse:
    """
    Synthesizes health status across:
    1. Core Application
    2. Database (PostgreSQL)
    3. Queue (Redis)
    4. Worker (Celery)
    """
    db_result = await check_database_connection()
    queue_result = await check_redis_queue_connection()
    worker_result = check_worker_cluster()

    db_connected = db_result.get("status") == "connected"
    queue_connected = queue_result.get("status") == "connected"
    worker_connected = worker_result.get("status") == "connected"

    if db_connected and queue_connected and worker_connected:
        overall_status = "healthy"
    elif db_connected and queue_connected:
        # Worker being absent in local dev or scaling can be degraded rather than down
        overall_status = "degraded"
    elif db_connected or queue_connected:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthStatusResponse(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
        application=ServiceComponentStatus(
            status="connected",
            latency_ms=0.0,
            details="FastAPI operational",
        ),
        database=ServiceComponentStatus(**db_result),
        queue=ServiceComponentStatus(**queue_result),
        worker=WorkerHealthStatus(**worker_result),
        meta={
            "app_name": settings.PROJECT_NAME,
            "api_prefix": settings.API_V1_PREFIX,
        },
    )
