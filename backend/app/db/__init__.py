"""Database session and declarative base."""
from app.db.base import Base, TimeStampedModel
from app.db.session import engine, AsyncSessionLocal, get_async_session

# Import all models to register with Base.metadata for Alembic auto-migrations
from app.modules.jobs.models import JobExecution
from app.modules.audit.models import AuditEvent
from app.modules.approvals.models import ApprovalRequest

__all__ = [
    "Base",
    "TimeStampedModel",
    "engine",
    "AsyncSessionLocal",
    "get_async_session",
    "JobExecution",
    "AuditEvent",
    "ApprovalRequest",
]
