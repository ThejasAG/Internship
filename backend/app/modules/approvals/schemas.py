from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from app.modules.approvals.models import ApprovalStatus


class ApprovalRequestCreate(BaseModel):
    action_type: str = Field(..., example="recruiter.outreach")
    payload: Dict[str, Any] = Field(..., example={"candidate_id": "c1", "company": "Acme Corp"})
    requested_by: str = Field(..., example="student_profile_1")
    expires_in_hours: Optional[int] = Field(72, description="Expiration TTL in hours")


class ApprovalDecisionRequest(BaseModel):
    decision: Literal["APPROVE", "REJECT"] = Field(..., example="APPROVE")
    actor_id: str = Field(..., example="user_advisor_1", description="Authenticated actor making the decision")
    decision_reason: Optional[str] = Field(None, description="Optional justification for decision")
    payload_hash_verification: Optional[str] = Field(
        None,
        description="Optional client-provided SHA-256 hash to assert payload consistency",
    )


class ApprovalResponse(BaseModel):
    id: str
    action_type: str
    payload: Dict[str, Any]
    payload_hash: str
    status: ApprovalStatus
    requested_by: str
    approved_by: Optional[str] = None
    decision_reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    execution_job_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
