import uuid
from unittest.mock import MagicMock, patch
import pytest
from httpx import AsyncClient
from app.worker.tasks import (
    test_automation_task,
    scheduled_heartbeat_task,
    TransientTaskError,
)
from app.worker.celery_app import celery_app


@pytest.mark.asyncio
async def test_enqueue_test_job(async_client: AsyncClient):
    with patch("app.api.v1.endpoints.jobs.test_automation_task.apply_async") as mock_apply:
        response = await async_client.post(
            "/api/v1/jobs/test",
            json={
                "task_name": "jobs.test_automation_task",
                "idempotency_key": "idemp-001",
                "payload": {"param": "value"},
                "simulate_transient_failure": False,
            },
            headers={"X-Correlation-ID": "test-cid-123"},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["task_name"] == "jobs.test_automation_task"
        assert data["idempotency_key"] == "idemp-001"
        assert data["status"] == "PENDING"
        assert data["correlation_id"] == "test-cid-123"
        mock_apply.assert_called_once()


@pytest.mark.asyncio
async def test_enqueue_job_idempotency(async_client: AsyncClient):
    with patch("app.api.v1.endpoints.jobs.test_automation_task.apply_async") as mock_apply:
        # First enqueue
        res1 = await async_client.post(
            "/api/v1/jobs/test",
            json={"idempotency_key": "idemp-unique-key", "payload": {"try": 1}},
        )
        assert res1.status_code == 202
        job1_id = res1.json()["id"]

        # Second enqueue with identical idempotency key
        res2 = await async_client.post(
            "/api/v1/jobs/test",
            json={"idempotency_key": "idemp-unique-key", "payload": {"try": 2}},
        )
        assert res2.status_code == 202
        job2_id = res2.json()["id"]

        # Must return the same persistent job without re-triggering Celery apply_async
        assert job1_id == job2_id
        assert mock_apply.call_count == 1


@pytest.mark.asyncio
async def test_list_jobs(async_client: AsyncClient):
    with patch("app.api.v1.endpoints.jobs.test_automation_task.apply_async"):
        await async_client.post(
            "/api/v1/jobs/test",
            json={"payload": {"name": "job-listing-test"}},
        )
        response = await async_client.get("/api/v1/jobs")
        assert response.status_code == 200
        jobs = response.json()
        assert isinstance(jobs, list)
        assert len(jobs) >= 1


def test_test_automation_task_execution_success():
    """Unit test for test_automation_task successful execution logic."""
    mock_self = MagicMock()
    mock_self.request.id = str(uuid.uuid4())
    mock_self.request.retries = 0

    with patch("app.worker.tasks.update_job_status_sync"), \
         patch("app.worker.tasks.record_audit_sync"):
        result = test_automation_task(
            mock_self,
            payload={"test": "payload"},
            simulate_transient_failure=False,
            correlation_id="test-cid",
        )
        assert result["status"] == "completed"
        assert result["input_echo"] == {"test": "payload"}
        assert result["retries_performed"] == 0


def test_test_automation_task_transient_retry():
    """Unit test verifying transient failure raises TransientTaskError on first try."""
    mock_self = MagicMock()
    mock_self.request.id = str(uuid.uuid4())
    mock_self.request.retries = 0

    with patch("app.worker.tasks.update_job_status_sync"), \
         patch("app.worker.tasks.record_audit_sync"):
        with pytest.raises(TransientTaskError):
            test_automation_task(
                mock_self,
                payload={"test": "retry"},
                simulate_transient_failure=True,
                correlation_id="test-cid",
            )

    # Next attempt (retries = 1) should succeed
    mock_self.request.retries = 1
    with patch("app.worker.tasks.update_job_status_sync"), \
         patch("app.worker.tasks.record_audit_sync"):
        result = test_automation_task(
            mock_self,
            payload={"test": "retry"},
            simulate_transient_failure=True,
            correlation_id="test-cid",
        )
        assert result["status"] == "completed"
        assert result["retries_performed"] == 1


def test_scheduled_heartbeat_task_registration_and_run():
    """Verifies that scheduled_heartbeat_task is registered in Celery beat schedule and executes."""
    # 1. Assert Celery beat schedule registration
    beat_schedule = celery_app.conf.beat_schedule
    assert "heartbeat-every-minute" in beat_schedule
    assert beat_schedule["heartbeat-every-minute"]["task"] == "jobs.scheduled_heartbeat_task"

    # 2. Assert direct execution
    mock_self = MagicMock()
    mock_self.request.id = str(uuid.uuid4())
    with patch("app.worker.tasks._get_sync_session", return_value=None):
        result = scheduled_heartbeat_task(mock_self)
        assert result["heartbeat"] == "healthy"
        assert "timestamp" in result
