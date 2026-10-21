import time
import uuid
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, correlation_id_ctx
from app.api.v1.api import api_router

settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("internpilot.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifecycle events. Runs on startup and shutdown.
    """
    logger.info(
        "InternPilot AI backend starting up",
        extra={
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
            "api_prefix": settings.API_V1_PREFIX,
        },
    )
    yield
    logger.info("InternPilot AI backend shutting down gracefully")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="InternPilot AI Core Backend Service — Phase 1 Foundation & Automation Infrastructure",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS Middleware
origins = settings.BACKEND_CORS_ORIGINS
allowed_origins = [str(o) for o in origins] if isinstance(origins, list) else [str(origins)]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_and_process_time_middleware(request: Request, call_next):
    """
    HTTP middleware extracting or generating correlation ID,
    setting contextvars for structured logs, and measuring request latency.
    """
    cid = (
        request.headers.get("X-Correlation-ID")
        or request.headers.get("X-Request-ID")
        or str(uuid.uuid4())
    )
    token = correlation_id_ctx.set(cid)

    start_time = time.perf_counter()
    try:
        response = await call_next(request)
        process_time = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(process_time)
        response.headers["X-Correlation-ID"] = cid

        if request.url.path not in ["/api/v1/ping", "/ping"]:
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code} ({process_time}ms)",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": process_time,
                    "correlation_id": cid,
                },
            )
        return response
    finally:
        correlation_id_ctx.reset(token)


# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root_status() -> dict:
    """
    Root discovery endpoint providing application metadata and documentation links.
    """
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": f"{settings.API_V1_PREFIX}/docs",
        "health_url": f"{settings.API_V1_PREFIX}/health",
        "status": "operational",
    }
