from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.modules.jobs.models import JobStatus


class EnqueueTestJobRequest(BaseModel):
    task_name: Optional[str] = Field("jobs.test_automation_task", description="Target Celery task name")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key to prevent double execution")
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary task payload")
    simulate_transient_failure: bool = Field(False, description="Simulate transient failure to test retry mechanism")
    max_retries: int = Field(3, description="Maximum bounded retry limit")


class JobExecutionResponse(BaseModel):
    id: str
    task_id: str
    task_name: str
    idempotency_key: Optional[str] = None
    status: JobStatus
    retry_count: int
    max_retries: int
    is_transient_error: Optional[bool] = None
    payload: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    correlation_id: Optional[str] = None
    enqueued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
