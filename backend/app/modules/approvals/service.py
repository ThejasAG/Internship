import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status
from app.modules.approvals.models import ApprovalRequest, ApprovalStatus
from app.modules.approvals.schemas import ApprovalRequestCreate, ApprovalDecisionRequest
from app.modules.audit.service import record_audit_event
from app.modules.audit.schemas import AuditEventCreate


def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """
    Computes a deterministic canonical SHA-256 hash of a payload dictionary.
    """
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


async def create_approval_request(
    session: AsyncSession,
    request_in: ApprovalRequestCreate,
    correlation_id: Optional[str] = None,
) -> ApprovalRequest:
    payload_hash = compute_payload_hash(request_in.payload)
    expires_at = None
    if request_in.expires_in_hours:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=request_in.expires_in_hours)

    approval = ApprovalRequest(
        action_type=request_in.action_type,
        payload=request_in.payload,
        payload_hash=payload_hash,
        status=ApprovalStatus.PENDING,
        requested_by=request_in.requested_by,
        expires_at=expires_at,
    )
    session.add(approval)
    await session.commit()
    await session.refresh(approval)

    # Emit immutable audit event
    await record_audit_event(
        session=session,
        event_in=AuditEventCreate(
            actor_type="user",
            actor_id=request_in.requested_by,
            action="approval.created",
            entity_type="approval_request",
            entity_id=approval.id,
            correlation_id=correlation_id,
            outcome="SUCCESS",
            payload_snapshot={"payload_hash": payload_hash, "action_type": approval.action_type},
        ),
    )
    return approval


async def get_approval_by_id(
    session: AsyncSession,
    approval_id: str,
) -> Optional[ApprovalRequest]:
    stmt = select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    result = await session.execute(stmt)
    approval = result.scalar_one_or_none()

    # Check for expiration on read
    if approval and approval.status == ApprovalStatus.PENDING and approval.expires_at:
        if datetime.now(timezone.utc) > approval.expires_at:
            approval.status = ApprovalStatus.EXPIRED
            await session.commit()
            await session.refresh(approval)

    return approval


async def process_approval_decision(
    session: AsyncSession,
    approval_id: str,
    decision_in: ApprovalDecisionRequest,
    correlation_id: Optional[str] = None,
) -> ApprovalRequest:
    approval = await get_approval_by_id(session, approval_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request '{approval_id}' not found",
        )

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot decide on approval in state '{approval.status}'",
        )

    # Cryptographic payload verification
    current_hash = compute_payload_hash(approval.payload)
    if current_hash != approval.payload_hash:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payload hash integrity check failed: payload was modified",
        )

    if (
        decision_in.payload_hash_verification
        and decision_in.payload_hash_verification != approval.payload_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client payload hash does not match immutable stored hash",
        )

    new_status = (
        ApprovalStatus.APPROVED
        if decision_in.decision.upper() == "APPROVE"
        else ApprovalStatus.REJECTED
    )

    approval.status = new_status
    approval.approved_by = decision_in.actor_id
    approval.decision_reason = decision_in.decision_reason
    approval.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(approval)

    # Record decision audit event
    await record_audit_event(
        session=session,
        event_in=AuditEventCreate(
            actor_type="user",
            actor_id=decision_in.actor_id,
            action=f"approval.{new_status.value.lower()}",
            entity_type="approval_request",
            entity_id=approval.id,
            correlation_id=correlation_id,
            outcome="SUCCESS",
            payload_snapshot={
                "payload_hash": approval.payload_hash,
                "reason": decision_in.decision_reason,
            },
        ),
    )

    return approval


async def mark_approval_executed(
    session: AsyncSession,
    approval_id: str,
    execution_job_id: str,
    correlation_id: Optional[str] = None,
) -> ApprovalRequest:
    approval = await get_approval_by_id(session, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if approval.status != ApprovalStatus.APPROVED:
        raise HTTPException(status_code=409, detail="Only APPROVED actions can be executed")

    approval.status = ApprovalStatus.EXECUTED
    approval.execution_job_id = execution_job_id
    approval.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(approval)

    await record_audit_event(
        session=session,
        event_in=AuditEventCreate(
            actor_type="system",
            actor_id="execution_engine",
            action="approval.executed",
            entity_type="approval_request",
            entity_id=approval.id,
            correlation_id=correlation_id,
            outcome="SUCCESS",
            payload_snapshot={"execution_job_id": execution_job_id},
        ),
    )
    return approval


async def list_recent_approvals(
    session: AsyncSession,
    limit: int = 50,
) -> List[ApprovalRequest]:
    stmt = select(ApprovalRequest).order_by(desc(ApprovalRequest.created_at)).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())
