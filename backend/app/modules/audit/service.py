from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.modules.audit.models import AuditEvent
from app.modules.audit.schemas import AuditEventCreate


async def record_audit_event(
    session: AsyncSession,
    event_in: AuditEventCreate,
) -> AuditEvent:
    """
    Appends an immutable audit event to the persistent audit log.
    """
    event = AuditEvent(
        actor_type=event_in.actor_type,
        actor_id=event_in.actor_id,
        action=event_in.action,
        entity_type=event_in.entity_type,
        entity_id=event_in.entity_id,
        correlation_id=event_in.correlation_id,
        outcome=event_in.outcome,
        payload_snapshot=event_in.payload_snapshot,
        metadata_snapshot=event_in.metadata_snapshot,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def get_recent_audit_events(
    session: AsyncSession,
    limit: int = 50,
) -> List[AuditEvent]:
    """
    Retrieves the most recent audit events ordered descending by timestamp.
    """
    stmt = select(AuditEvent).order_by(desc(AuditEvent.timestamp)).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())
