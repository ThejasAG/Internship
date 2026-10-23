import pytest
from httpx import AsyncClient
from app.modules.approvals.service import compute_payload_hash


@pytest.mark.asyncio
async def test_compute_payload_hash_deterministic():
    p1 = {"b": 2, "a": 1}
    p2 = {"a": 1, "b": 2}
    # Deterministic regardless of dict key order
    assert compute_payload_hash(p1) == compute_payload_hash(p2)


@pytest.mark.asyncio
async def test_approval_lifecycle_approve(async_client: AsyncClient):
    payload = {"student_id": "std_101", "role": "Software Engineering Intern"}
    expected_hash = compute_payload_hash(payload)

    # 1. Create approval request
    create_res = await async_client.post(
        "/api/v1/approvals",
        json={
            "action_type": "application.submit",
            "payload": payload,
            "requested_by": "student_101",
            "expires_in_hours": 24,
        },
        headers={"X-Correlation-ID": "corr-appr-1"},
    )
    assert create_res.status_code == 201
    appr_data = create_res.json()
    approval_id = appr_data["id"]
    assert appr_data["status"] == "PENDING"
    assert appr_data["payload_hash"] == expected_hash

    # 2. Get approval by ID
    get_res = await async_client.get(f"/api/v1/approvals/{approval_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == approval_id

    # 3. Approve with authenticated actor
    decision_res = await async_client.post(
        f"/api/v1/approvals/{approval_id}/decision",
        json={
            "decision": "APPROVE",
            "actor_id": "advisor_user_99",
            "decision_reason": "Resume vetted and approved",
            "payload_hash_verification": expected_hash,
        },
    )
    assert decision_res.status_code == 200
    decided = decision_res.json()
    assert decided["status"] == "APPROVED"
    assert decided["approved_by"] == "advisor_user_99"
    assert decided["decision_reason"] == "Resume vetted and approved"


@pytest.mark.asyncio
async def test_approval_lifecycle_reject(async_client: AsyncClient):
    payload = {"recipient": "recruiter@example.com", "text": "Outreach message"}
    create_res = await async_client.post(
        "/api/v1/approvals",
        json={
            "action_type": "recruiter.outreach",
            "payload": payload,
            "requested_by": "student_202",
        },
    )
    approval_id = create_res.json()["id"]

    reject_res = await async_client.post(
        f"/api/v1/approvals/{approval_id}/decision",
        json={
            "decision": "REJECT",
            "actor_id": "compliance_bot",
            "decision_reason": "Tone requires adjustment",
        },
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "REJECTED"


@pytest.mark.asyncio
async def test_approval_hash_mismatch_rejection(async_client: AsyncClient):
    payload = {"target": "company_x"}
    create_res = await async_client.post(
        "/api/v1/approvals",
        json={
            "action_type": "audit.test",
            "payload": payload,
            "requested_by": "user_1",
        },
    )
    approval_id = create_res.json()["id"]

    # Attempting to decide with mismatched hash assertion
    bad_res = await async_client.post(
        f"/api/v1/approvals/{approval_id}/decision",
        json={
            "decision": "APPROVE",
            "actor_id": "admin_1",
            "payload_hash_verification": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    )
    assert bad_res.status_code == 400
    assert "Client payload hash does not match" in bad_res.json()["detail"]


@pytest.mark.asyncio
async def test_unknown_decision_is_rejected_not_recorded(async_client: AsyncClient):
    create_res = await async_client.post(
        "/api/v1/approvals",
        json={"action_type": "application.submit", "payload": {"x": 1}, "requested_by": "student_1"},
    )
    approval_id = create_res.json()["id"]

    # "approved" used to be stored silently as REJECTED
    res = await async_client.post(
        f"/api/v1/approvals/{approval_id}/decision",
        json={"decision": "approved", "actor_id": "advisor_1"},
    )
    assert res.status_code == 422
    assert (await async_client.get(f"/api/v1/approvals/{approval_id}")).json()["status"] == "PENDING"
