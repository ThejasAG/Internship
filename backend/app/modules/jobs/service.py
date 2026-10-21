import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.modules.jobs.models import JobExecution, JobStatus


async def get_job_by_idempotency_key(
    session: AsyncSession,
    idempotency_key: str,
) -> Optional[JobExecution]:
    """
    Finds existing job execution by idempotency key to prevent double execution.
    """
    stmt = select(JobExecution).where(JobExecution.idempotency_key == idempotency_key)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_job_by_id(
    session: AsyncSession,
    job_id: str,
) -> Optional[JobExecution]:
    stmt = select(JobExecution).where(JobExecution.id == job_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_job_by_task_id(
    session: AsyncSession,
    task_id: str,
) -> Optional[JobExecution]:
    stmt = select(JobExecution).where(JobExecution.task_id == task_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_job_execution(
    session: AsyncSession,
    task_id: str,
    task_name: str,
    idempotency_key: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    correlation_id: Optional[str] = None,
) -> JobExecution:
    """
    Persists initial job execution record with PENDING status.
    """
    job = JobExecution(
        id=str(uuid.uuid4()),
        task_id=task_id,
        task_name=task_name,
        idempotency_key=idempotency_key,
        status=JobStatus.PENDING,
        retry_count=0,
        max_retries=max_retries,
        payload=payload,
        correlation_id=correlation_id,
        enqueued_at=datetime.now(timezone.utc),
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def list_recent_jobs(
    session: AsyncSession,
    limit: int = 50,
) -> List[JobExecution]:
    stmt = select(JobExecution).order_by(desc(JobExecution.enqueued_at)).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())
