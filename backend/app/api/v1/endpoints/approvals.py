import uuid
from typing import List
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.modules.approvals.schemas import (
    ApprovalRequestCreate,
    ApprovalDecisionRequest,
    ApprovalResponse,
)
from app.modules.approvals.service import (
    create_approval_request,
    get_approval_by_id,
    process_approval_decision,
    list_recent_approvals,
)

router = APIRouter()


@router.post(
    "",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create approval request",
    description="Generates an approval item bound to an immutable SHA-256 payload hash.",
)
async def create_approval(
    request_in: ApprovalRequestCreate,
    session: AsyncSession = Depends(get_async_session),
    x_correlation_id: str = Header(default=None),
) -> ApprovalResponse:
    cid = x_correlation_id or str(uuid.uuid4())
    return await create_approval_request(session, request_in, correlation_id=cid)


@router.get(
    "",
    response_model=List[ApprovalResponse],
    summary="List recent approvals",
)
async def list_approvals(
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session),
) -> List[ApprovalResponse]:
    return await list_recent_approvals(session, limit=limit)


@router.get(
    "/{approval_id}",
    response_model=ApprovalResponse,
    summary="Get approval request by ID",
)
async def get_approval(
    approval_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> ApprovalResponse:
    approval = await get_approval_by_id(session, approval_id)
    if not approval:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request '{approval_id}' not found",
        )
    return approval


@router.post(
    "/{approval_id}/decision",
    response_model=ApprovalResponse,
    summary="Decide on approval request",
    description="Submits an approval decision (APPROVE/REJECT) verifying payload cryptographic hash integrity.",
)
async def decide_approval(
    approval_id: str,
    decision_in: ApprovalDecisionRequest,
    session: AsyncSession = Depends(get_async_session),
    x_correlation_id: str = Header(default=None),
) -> ApprovalResponse:
    cid = x_correlation_id or str(uuid.uuid4())
    return await process_approval_decision(
        session=session,
        approval_id=approval_id,
        decision_in=decision_in,
        correlation_id=cid,
    )
