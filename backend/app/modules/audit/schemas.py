from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AuditEventCreate(BaseModel):
    actor_type: str = Field(..., example="system")
    actor_id: str = Field(..., example="api_worker_1")
    action: str = Field(..., example="job.enqueued")
    entity_type: str = Field(..., example="job_execution")
    entity_id: str = Field(..., example="job-123")
    correlation_id: Optional[str] = Field(None, example="req-456")
    outcome: str = Field(..., example="SUCCESS")
    payload_snapshot: Optional[Dict[str, Any]] = None
    metadata_snapshot: Optional[Dict[str, Any]] = None


class AuditEventResponse(BaseModel):
    id: str
    actor_type: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    correlation_id: Optional[str] = None
    outcome: str
    payload_snapshot: Optional[Dict[str, Any]] = None
    metadata_snapshot: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True
