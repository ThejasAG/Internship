import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AuditEvent(Base):
    """
    Append-only immutable audit trail record.
    Captures actor, action, entity, timestamp, outcome, and correlation ID.
    """
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)  # user, system, worker, api
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'job.enqueued', 'approval.created'
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'job_execution', 'approval_request'
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)  # SUCCESS, FAILURE
    payload_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    metadata_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
