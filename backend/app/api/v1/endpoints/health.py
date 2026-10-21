from fastapi import APIRouter, status, Response
from app.modules.health.schemas import HealthStatusResponse
from app.modules.health.service import get_system_health

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthStatusResponse,
    summary="Comprehensive system health probe",
    description="Inspects API uptime, PostgreSQL connectivity (via SELECT 1), and Redis availability.",
    tags=["Health & Diagnostics"],
)
async def check_health(response: Response) -> HealthStatusResponse:
    health_data = await get_system_health()
    if health_data.status == "unhealthy":
        response.status_code = status.HTTP(503)
    else:
        response.status_code = status.HTTP_200_OK
    return health_data


@router.get(
    "/ping",
    summary="Lightweight liveness probe",
    description="Immediate response verifying the web application process is responsive.",
    tags=["Health & Diagnostics"],
)
async def liveness_probe() -> dict:
    return {"status": "ok", "message": "pong"}
