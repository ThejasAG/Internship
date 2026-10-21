import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.modules.jobs.models import JobStatus
from app.modules.jobs.schemas import (
    EnqueueTestJobRequest,
    JobExecutionResponse,
)
from app.modules.jobs.service import (
    get_job_by_id,
    get_job_by_idempotency_key,
    create_job_execution,
    list_recent_jobs,
)
from app.modules.audit.service import record_audit_event
from app.modules.audit.schemas import AuditEventCreate
from app.worker.tasks import test_automation_task

router = APIRouter()


@router.post(
    "/test",
    response_model=JobExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue test background task",
    description="Enqueues an idempotent background job, records persistent JobExecution state, and emits an audit event.",
)
async def enqueue_test_job(
    request: EnqueueTestJobRequest,
    session: AsyncSession = Depends(get_async_session),
    x_correlation_id: str = Header(default=None),
) -> JobExecutionResponse:
    cid = x_correlation_id or str(uuid.uuid4())

    # Idempotency check
    if request.idempotency_key:
        existing = await get_job_by_idempotency_key(session, request.idempotency_key)
        if existing:
            # If already pending, running, or succeeded, return existing record
            return existing

    task_id = str(uuid.uuid4())
    job = await create_job_execution(
        session=session,
        task_id=task_id,
        task_name=request.task_name or "jobs.test_automation_task",
        idempotency_key=request.idempotency_key,
        payload=request.payload,
        max_retries=request.max_retries,
        correlation_id=cid,
    )

    # Emit audit event for enqueued task
    await record_audit_event(
        session=session,
        event_in=AuditEventCreate(
            actor_type="api",
            actor_id="test_trigger",
            action="job.enqueued",
            entity_type="job_execution",
            entity_id=job.id,
            correlation_id=cid,
            outcome="SUCCESS",
            payload_snapshot={
                "task_name": job.task_name,
                "task_id": task_id,
                "idempotency_key": request.idempotency_key,
            },
        ),
    )

    # Enqueue task to Celery
    try:
        test_automation_task.apply_async(
            kwargs={
                "payload": request.payload or {},
                "idempotency_key": request.idempotency_key,
                "simulate_transient_failure": request.simulate_transient_failure,
                "correlation_id": cid,
            },
            task_id=task_id,
        )
    except Exception as exc:
        # Fallback if Redis is offline during local test
        job.status = JobStatus.FAILED
        job.error_message = f"Failed to enqueue to Celery broker: {exc}"
        await session.commit()
        await session.refresh(job)

    return job


@router.get(
    "",
    response_model=List[JobExecutionResponse],
    summary="List recent job executions",
)
async def list_jobs(
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session),
) -> List[JobExecutionResponse]:
    return await list_recent_jobs(session, limit=limit)


@router.get(
    "/{job_id}",
    response_model=JobExecutionResponse,
    summary="Get job execution by ID",
)
async def get_job(
    job_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> JobExecutionResponse:
    job = await get_job_by_id(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job execution '{job_id}' not found",
        )
    return job
