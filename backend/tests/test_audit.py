import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.audit.schemas import AuditEventCreate
from app.modules.audit.service import record_audit_event, get_recent_audit_events


@pytest.mark.asyncio
async def test_audit_event_persistence(db_session: AsyncSession):
    event_in = AuditEventCreate(
        actor_type="system",
        actor_id="test_worker_1",
        action="security.scan_completed",
        entity_type="target_repo",
        entity_id="repo_99",
        correlation_id="corr-audit-999",
        outcome="SUCCESS",
        payload_snapshot={"scanned_items": 42},
        metadata_snapshot={"env": "test"},
    )
    event = await record_audit_event(db_session, event_in)
    assert event.id is not None
    assert event.actor_id == "test_worker_1"
    assert event.action == "security.scan_completed"
    assert event.outcome == "SUCCESS"
    assert event.correlation_id == "corr-audit-999"
    assert event.timestamp is not None

    events = await get_recent_audit_events(db_session, limit=10)
    assert any(e.id == event.id for e in events)


@pytest.mark.asyncio
async def test_audit_api_endpoint(async_client: AsyncClient):
    # Trigger an action that creates an audit event (such as creating an approval)
    await async_client.post(
        "/api/v1/approvals",
        json={
            "action_type": "audit.verification",
            "payload": {"key": "test_audit"},
            "requested_by": "audit_tester",
        },
        headers={"X-Correlation-ID": "corr-api-audit-1"},
    )

    response = await async_client.get("/api/v1/audit")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) >= 1
    found = any(e.get("action") == "approval.created" for e in events)
    assert found
