from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ServiceComponentStatus(BaseModel):
    """Status details for a backing infrastructure component."""
    status: str = Field(..., description="'connected', 'disconnected', or 'degraded'")
    latency_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    details: Optional[str] = Field(None, description="Diagnostic detail or status message")
    error: Optional[str] = Field(None, description="Error message if disconnected")


class WorkerHealthStatus(BaseModel):
    """Celery worker cluster health status."""
    status: str = Field(..., description="'connected' or 'disconnected'")
    active_workers: List[str] = Field(default_factory=list, description="Names of responding worker nodes")
    worker_count: int = Field(0, description="Total active worker nodes detected")
    details: Optional[str] = None
    error: Optional[str] = None


class HealthStatusResponse(BaseModel):
    """
    Unified multi-tier system health check response model distinguishing
    Application, Database, Queue, and Background Worker availability.
    """
    status: str = Field(..., description="'healthy', 'degraded', or 'unhealthy'")
    environment: str = Field(..., description="Active runtime environment")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Timestamp of the health assessment")
    application: ServiceComponentStatus = Field(..., description="FastAPI core application status")
    database: ServiceComponentStatus = Field(..., description="PostgreSQL database connectivity")
    queue: ServiceComponentStatus = Field(..., description="Redis queue/broker connectivity")
    worker: WorkerHealthStatus = Field(..., description="Celery background worker cluster status")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Operational metadata")
