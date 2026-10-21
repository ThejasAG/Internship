import time
from typing import AsyncGenerator, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import get_settings

settings = get_settings()

# Engine creation with connection pool settings suited for production workloads
engine = create_async_engine(
    settings.DATABASE_URL or "postgresql+asyncpg://postgres:postgres@localhost:5432/internpilot",
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"timeout": 5} if "sqlite" not in (settings.DATABASE_URL or "") else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding a managed async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection() -> Dict[str, Any]:
    """
    Executes a lightweight query (SELECT 1) to verify live database connectivity
    and measures query latency in milliseconds.
    """
    start_time = time.perf_counter()
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            scalar = result.scalar()
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if scalar == 1:
                return {
                    "status": "connected",
                    "latency_ms": latency_ms,
                    "details": "Database responding normally",
                }
            return {
                "status": "degraded",
                "latency_ms": latency_ms,
                "details": f"Unexpected ping response: {scalar}",
            }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "disconnected",
            "latency_ms": latency_ms,
            "error": str(exc),
        }
