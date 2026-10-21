from unittest.mock import patch
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "InternPilot AI API"
    assert data["status"] == "operational"
    assert "health_url" in data


@pytest.mark.asyncio
async def test_ping_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "pong"}


@pytest.mark.asyncio
async def test_health_endpoint_healthy(async_client: AsyncClient):
    with patch(
        "app.modules.health.service.check_database_connection",
        return_value={"status": "connected", "latency_ms": 1.25, "details": "Database OK"},
    ), patch(
        "app.modules.health.service.check_redis_queue_connection",
        return_value={"status": "connected", "latency_ms": 0.85, "details": "Redis OK"},
    ), patch(
        "app.modules.health.service.check_worker_cluster",
        return_value={"status": "connected", "active_workers": ["worker1@host"], "worker_count": 1},
    ):
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["application"]["status"] == "connected"
        assert data["database"]["status"] == "connected"
        assert data["queue"]["status"] == "connected"
        assert data["worker"]["status"] == "connected"
        assert data["worker"]["worker_count"] == 1


@pytest.mark.asyncio
async def test_health_endpoint_degraded(async_client: AsyncClient):
    with patch(
        "app.modules.health.service.check_database_connection",
        return_value={"status": "connected", "latency_ms": 2.1, "details": "Database OK"},
    ), patch(
        "app.modules.health.service.check_redis_queue_connection",
        return_value={"status": "connected", "latency_ms": 1.1, "details": "Redis OK"},
    ), patch(
        "app.modules.health.service.check_worker_cluster",
        return_value={"status": "disconnected", "active_workers": [], "worker_count": 0},
    ):
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"]["status"] == "connected"
        assert data["worker"]["status"] == "disconnected"


@pytest.mark.asyncio
async def test_health_endpoint_unhealthy(async_client: AsyncClient):
    with patch(
        "app.modules.health.service.check_database_connection",
        return_value={"status": "disconnected", "latency_ms": 500.0, "error": "Database down"},
    ), patch(
        "app.modules.health.service.check_redis_queue_connection",
        return_value={"status": "disconnected", "latency_ms": 500.0, "error": "Redis down"},
    ), patch(
        "app.modules.health.service.check_worker_cluster",
        return_value={"status": "disconnected", "active_workers": [], "worker_count": 0},
    ):
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"]["status"] == "disconnected"
        assert data["queue"]["status"] == "disconnected"
