import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.worker.celery_app import celery_app
from app.modules.jobs.models import JobExecution, JobStatus
from app.modules.audit.models import AuditEvent

logger = logging.getLogger("internpilot.worker.tasks")
settings = get_settings()

# Sync engine for Celery worker processes
_sync_url = settings.SYNC_DATABASE_URL or ""
if not _sync_url and settings.DATABASE_URL:
    _sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

_sync_engine = None
if _sync_url and "sqlite" not in _sync_url:
    try:
        _sync_engine = create_engine(_sync_url, pool_pre_ping=True)
    except Exception as e:
        logger.warning(f"Could not initialize sync engine for worker: {e}")


class TransientTaskError(Exception):
    """Temporary failure eligible for bounded exponential backoff retries."""
    pass


class PermanentTaskError(Exception):
    """Unrecoverable failure that should terminate execution without retry."""
    pass


def _get_sync_session():
    if _sync_engine is not None:
        return Session(_sync_engine)
    return None


def update_job_status_sync(
    task_id: str,
    status: JobStatus,
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    is_transient: Optional[bool] = None,
    retry_count: Optional[int] = None,
    started: bool = False,
    completed: bool = False,
) -> Optional[JobExecution]:
    """
    Synchronously updates JobExecution in PostgreSQL from within Celery worker.
    """
    session = _get_sync_session()
    if session is None:
        return None

    try:
        stmt = select(JobExecution).where(JobExecution.task_id == task_id)
        job = session.execute(stmt).scalar_one_or_none()
        if job:
            job.status = status
            if retry_count is not None:
                job.retry_count = retry_count
            if is_transient is not None:
                job.is_transient_error = is_transient
            if started and not job.started_at:
                job.started_at = datetime.now(timezone.utc)
            if completed:
                job.completed_at = datetime.now(timezone.utc)
            if result is not None:
                job.result = result
            if error_message is not None:
                job.error_message = error_message
            session.commit()
            return job
        return None
    except Exception as exc:
        logger.error(f"Failed to update job status in DB: {exc}")
        session.rollback()
        return None
    finally:
        session.close()


def record_audit_sync(
    actor_id: str,
    action: str,
    entity_id: str,
    outcome: str,
    correlation_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
):
    session = _get_sync_session()
    if session is None:
        return

    try:
        event = AuditEvent(
            actor_type="worker",
            actor_id=actor_id,
            action=action,
            entity_type="job_execution",
            entity_id=entity_id,
            correlation_id=correlation_id,
            outcome=outcome,
            payload_snapshot=payload,
            timestamp=datetime.now(timezone.utc),
        )
        session.add(event)
        session.commit()
    except Exception as exc:
        logger.error(f"Failed to record audit event in worker: {exc}")
        session.rollback()
    finally:
        session.close()


@celery_app.task(
    bind=True,
    name="jobs.test_automation_task",
    max_retries=3,
    autoretry_for=(TransientTaskError,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=False,
)
def test_automation_task(
    self,
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = None,
    simulate_transient_failure: bool = False,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Idempotent, bounded-retry background task demonstrating execution tracking,
    retry telemetry, and audit event persistence.
    """
    task_id = self.request.id
    current_retry = self.request.retries
    logger.info(
        f"Executing test_automation_task [task_id={task_id}, retry={current_retry}]",
        extra={"task_id": task_id, "correlation_id": correlation_id},
    )

    # 1. Check idempotency: if job is already SUCCESS, return immediately
    session = _get_sync_session()
    if session and idempotency_key:
        try:
            stmt = select(JobExecution).where(JobExecution.idempotency_key == idempotency_key)
            existing = session.execute(stmt).scalar_one_or_none()
            if existing and existing.status == JobStatus.SUCCESS and existing.task_id != task_id:
                logger.info(f"Task with idempotency key '{idempotency_key}' already completed. Skipping duplicate execution.")
                return existing.result or {"status": "already_executed"}
        finally:
            session.close()

    # 2. Mark running
    update_job_status_sync(
        task_id=task_id,
        status=JobStatus.RUNNING,
        started=True,
        retry_count=current_retry,
    )

    # 3. Simulate transient failure if requested (only on first attempt)
    if simulate_transient_failure and current_retry == 0:
        logger.warning(
            f"Simulating transient failure for task_id={task_id} (retry 0 -> retry 1)",
            extra={"task_id": task_id, "correlation_id": correlation_id},
        )
        update_job_status_sync(
            task_id=task_id,
            status=JobStatus.RETRYING,
            is_transient=True,
            retry_count=1,
            error_message="Transient network glitch simulated for reliability testing",
        )
        record_audit_sync(
            actor_id="celery_worker",
            action="job.retrying",
            entity_id=task_id,
            outcome="FAILURE",
            correlation_id=correlation_id,
            payload={"reason": "simulated_transient_failure", "retry": 1},
        )
        raise TransientTaskError("Simulated transient connection failure")

    # 4. Successful execution
    result = {
        "status": "completed",
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "input_echo": payload,
        "task_id": task_id,
        "retries_performed": current_retry,
    }

    update_job_status_sync(
        task_id=task_id,
        status=JobStatus.SUCCESS,
        result=result,
        completed=True,
        retry_count=current_retry,
    )

    record_audit_sync(
        actor_id="celery_worker",
        action="job.completed",
        entity_id=task_id,
        outcome="SUCCESS",
        correlation_id=correlation_id,
        payload=result,
    )

    logger.info(f"test_automation_task completed successfully [task_id={task_id}]")
    return result


@celery_app.task(bind=True, name="jobs.scheduled_heartbeat_task")
def scheduled_heartbeat_task(self) -> Dict[str, Any]:
    """
    Periodic task scheduled via Celery Beat, recording automated heartbeats
    into persistent job storage and audit trail.
    """
    task_id = self.request.id
    now = datetime.now(timezone.utc)
    logger.info(f"Executing scheduled_heartbeat_task [task_id={task_id}]")

    session = _get_sync_session()
    if session:
        try:
            job = JobExecution(
                id=str(uuid.uuid4()),
                task_id=task_id,
                task_name="jobs.scheduled_heartbeat_task",
                status=JobStatus.SUCCESS,
                retry_count=0,
                max_retries=1,
                payload={"heartbeat_interval_sec": 60},
                result={"heartbeat": "pulse", "executed_at": now.isoformat()},
                enqueued_at=now,
                started_at=now,
                completed_at=now,
            )
            session.add(job)

            audit = AuditEvent(
                actor_type="system",
                actor_id="celery_beat",
                action="scheduled.heartbeat",
                entity_type="job_execution",
                entity_id=job.id,
                outcome="SUCCESS",
                payload_snapshot={"task_id": task_id},
                timestamp=now,
            )
            session.add(audit)
            session.commit()
        except Exception as exc:
            logger.error(f"Error persisting scheduled heartbeat: {exc}")
            session.rollback()
        finally:
            session.close()

    return {"heartbeat": "healthy", "timestamp": now.isoformat()}
