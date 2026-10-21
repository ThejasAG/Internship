from fastapi import APIRouter
from app.api.v1.endpoints import health, jobs, approvals, audit

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["Health & Diagnostics"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs & Automation"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Trail"])
