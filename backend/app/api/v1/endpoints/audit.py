from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.modules.audit.schemas import AuditEventResponse
from app.modules.audit.service import get_recent_audit_events

router = APIRouter()


@router.get(
    "",
    response_model=List[AuditEventResponse],
    summary="List recent append-only audit events",
)
async def list_audit_events(
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session),
) -> List[AuditEventResponse]:
    return await get_recent_audit_events(session, limit=limit)
